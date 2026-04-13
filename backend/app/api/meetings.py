import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.meeting import InputType, Meeting, MeetingStatus
from app.models.user import User
from app.schemas.meeting import MeetingList, MeetingRead
from app.tasks.worker import process_meeting_task

router = APIRouter(prefix="/meetings", tags=["meetings"])

AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a"}
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm"}
TEXT_EXTENSIONS = {".txt", ".docx"}


def _get_input_type(filename: str) -> InputType:
    ext = os.path.splitext(filename)[1].lower()
    if ext in AUDIO_EXTENSIONS:
        return InputType.AUDIO
    if ext in VIDEO_EXTENSIONS:
        return InputType.VIDEO
    if ext in TEXT_EXTENSIONS:
        return InputType.TEXT
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Неподдерживаемый формат файла: {ext}",
    )


def _check_file_size(size: int, input_type: InputType):
    max_mb = (
        settings.MAX_VIDEO_SIZE_MB if input_type == InputType.VIDEO
        else settings.MAX_AUDIO_SIZE_MB
    )
    if size > max_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Файл слишком большой. Максимальный размер: {max_mb} МБ",
        )


@router.post("/upload", response_model=MeetingRead, status_code=status.HTTP_201_CREATED)
async def upload_meeting(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload audio, video, or text file to create a new meeting."""
    input_type = _get_input_type(file.filename)

    content = await file.read()
    _check_file_size(len(content), input_type)

    # Save file to disk
    user_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(user_dir, filename)

    with open(file_path, "wb") as f:
        f.write(content)

    meeting = Meeting(
        user_id=current_user.id,
        title=title,
        input_type=input_type,
        original_file_url=file_path,
        status=MeetingStatus.PENDING,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    process_meeting_task.delay(meeting.id)

    return meeting


@router.post("/text", response_model=MeetingRead, status_code=status.HTTP_201_CREATED)
def create_text_meeting(
    title: str = Form(...),
    text: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a meeting from pasted text."""
    meeting = Meeting(
        user_id=current_user.id,
        title=title,
        input_type=InputType.TEXT,
        transcript=text,
        status=MeetingStatus.PENDING,
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    process_meeting_task.delay(meeting.id)

    return meeting


@router.get("/", response_model=list[MeetingList])
def list_meetings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all meetings for the current user."""
    meetings = (
        db.query(Meeting)
        .filter(Meeting.user_id == current_user.id)
        .order_by(Meeting.created_at.desc())
        .all()
    )
    return meetings


@router.get("/{meeting_id}", response_model=MeetingRead)
def get_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific meeting by ID (scoped to current user)."""
    meeting = (
        db.query(Meeting)
        .filter(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
        .first()
    )
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Совещание не найдено",
        )
    return meeting


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a meeting."""
    meeting = (
        db.query(Meeting)
        .filter(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
        .first()
    )
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Совещание не найдено",
        )
    # Clean up file if exists
    if meeting.original_file_url and os.path.exists(meeting.original_file_url):
        os.unlink(meeting.original_file_url)

    db.delete(meeting)
    db.commit()
