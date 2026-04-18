import logging
import os

from celery import Celery

from app.core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "meeting_processor",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(bind=True, max_retries=2)
def process_meeting_task(self, meeting_id: int):
    """Main async task: transcribe (if needed) and process via LLM."""
    from app.core.database import SessionLocal
    from app.models.meeting import Meeting, MeetingStatus, InputType
    from app.services.transcription import (
        extract_audio_from_video,
        read_text_file,
        transcribe,
    )
    from app.services.llm import process_transcript

    db = SessionLocal()
    try:
        meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
        if not meeting:
            logger.error(f"Meeting {meeting_id} not found")
            return

        user = meeting.user

        try:
            # Step 1: Transcription
            if meeting.input_type in (InputType.AUDIO, InputType.VIDEO):
                meeting.status = MeetingStatus.TRANSCRIBING
                db.commit()

                file_path = meeting.original_file_url
                audio_path = file_path

                if meeting.input_type == InputType.VIDEO:
                    audio_path = extract_audio_from_video(file_path)

                transcript = transcribe(
                    audio_path, provider=user.transcription_provider
                )

                # Clean up temp audio from video extraction
                if meeting.input_type == InputType.VIDEO and audio_path != file_path:
                    os.unlink(audio_path)

                meeting.transcript = transcript
                db.commit()

            elif meeting.input_type == InputType.TEXT:
                if meeting.original_file_url:
                    meeting.transcript = read_text_file(meeting.original_file_url)
                    db.commit()
                # If transcript was set directly, it's already in the DB

            # Step 2: LLM processing
            meeting.status = MeetingStatus.PROCESSING
            db.commit()

            result = process_transcript(
                meeting.transcript,
                user.system_prompt,
                provider=user.llm_provider,
                model=user.llm_model,
            )
            meeting.result_json = result
            meeting.status = MeetingStatus.DONE
            db.commit()

        except Exception as e:
            logger.exception(f"Error processing meeting {meeting_id}")
            meeting.status = MeetingStatus.FAILED
            meeting.error_message = str(e)
            db.commit()

    finally:
        db.close()
