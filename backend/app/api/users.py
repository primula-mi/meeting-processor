from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import DEFAULT_SYSTEM_PROMPT, User
from app.schemas.user import LLMSettingsUpdate, SystemPromptUpdate, UserRead
from app.services.llm import list_ollama_models

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


@router.put("/me/llm-settings", response_model=UserRead)
def update_llm_settings(
    body: LLMSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the user's LLM provider and model."""
    current_user.llm_provider = body.llm_provider
    current_user.llm_model = body.llm_model
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/available-models")
def get_available_models():
    """Return available LLM models grouped by provider."""
    openai_models = [
        {"id": "gpt-4o", "name": "GPT-4o"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo"},
    ]

    ollama_models = []
    raw = list_ollama_models()
    for m in raw:
        ollama_models.append({"id": m.get("name", ""), "name": m.get("name", "")})

    return {
        "default_provider": settings.LLM_PROVIDER,
        "providers": {
            "openai": {"name": "OpenAI", "models": openai_models},
            "ollama": {
                "name": "Ollama",
                "models": ollama_models,
                "available": len(ollama_models) > 0,
            },
        },
    }
