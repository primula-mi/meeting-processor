from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.meeting import InputType, MeetingStatus


class MeetingCreate(BaseModel):
    title: str


class MeetingRead(BaseModel):
    id: int
    title: str
    input_type: InputType
    status: MeetingStatus
    original_file_url: str | None
    transcript: str | None
    result_json: dict[str, Any] | None
    error_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MeetingList(BaseModel):
    id: int
    title: str
    input_type: InputType
    status: MeetingStatus
    created_at: datetime

    model_config = {"from_attributes": True}
