from datetime import datetime

from pydantic import BaseModel


class UserRead(BaseModel):
    id: int
    yandex_id: str | None
    bitrix24_id: str | None
    email: str | None
    name: str | None
    system_prompt: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SystemPromptUpdate(BaseModel):
    system_prompt: str
