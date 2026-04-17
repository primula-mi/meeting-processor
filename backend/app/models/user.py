from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

DEFAULT_SYSTEM_PROMPT = (
    "Ты бизнес-ассистент. Проанализируй транскрипт совещания и верни результат "
    "в формате JSON со следующими полями:\n"
    '- "summary": краткая выжимка совещания\n'
    '- "tasks": массив объектов с полями "task" (описание задачи), '
    '"assigner" (постановщик), "assignee" (ответственный, если определён), '
    '"deadline" (срок, если указан)\n'
    '- "decisions": список принятых решений\n\n'
    "Отвечай только валидным JSON, без дополнительного текста."
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Exactly one of yandex_id / bitrix24_id is set per user, depending on the auth provider used.
    yandex_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    bitrix24_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text, default=DEFAULT_SYSTEM_PROMPT)
    llm_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    meetings = relationship("Meeting", back_populates="user", cascade="all, delete-orphan")
