from datetime import datetime

from pydantic import BaseModel


class UserRead(BaseModel):
    id: int
    yandex_id: str | None
    bitrix24_id: str | None
    email: str | None
    name: str | None
    system_prompt: str
    llm_provider: str | None
    llm_model: str | None
    transcription_provider: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SystemPromptUpdate(BaseModel):
    system_prompt: str


class LLMSettingsUpdate(BaseModel):
    llm_provider: str
    llm_model: str


class TranscriptionSettingsUpdate(BaseModel):
    transcription_provider: str
