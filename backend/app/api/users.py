from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import DEFAULT_SYSTEM_PROMPT, User
from app.schemas.user import SystemPromptUpdate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the current authenticated user profile."""
    return current_user


@router.put("/me/system-prompt", response_model=UserRead)
def update_system_prompt(
    body: SystemPromptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the user's system prompt."""
    current_user.system_prompt = body.system_prompt
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/system-prompt/reset", response_model=UserRead)
def reset_system_prompt(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reset the system prompt to the default value."""
    current_user.system_prompt = DEFAULT_SYSTEM_PROMPT
    db.commit()
    db.refresh(current_user)
    return current_user
