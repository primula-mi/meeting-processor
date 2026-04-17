from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Meeting Processor"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/meeting_processor"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Yandex OAuth (primary, visible in UI)
    YANDEX_CLIENT_ID: str = ""
    YANDEX_CLIENT_SECRET: str = ""
    YANDEX_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/yandex/callback"
    # Comma-separated list of allowed corporate email domains for Yandex login.
    # Leave empty to allow any Yandex account (dev/testing only).
    ALLOWED_EMAIL_DOMAINS: str = ""

    # Bitrix24 OAuth (kept functional but disabled in UI — enable when a paid Bitrix24 plan is available)
    BITRIX24_CLIENT_ID: str = ""
    BITRIX24_CLIENT_SECRET: str = ""
    BITRIX24_DOMAIN: str = ""  # e.g. "company.bitrix24.ru"
    BITRIX24_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/bitrix24/callback"

    @property
    def allowed_domains_list(self) -> list[str]:
        return [d.strip().lower() for d in self.ALLOWED_EMAIL_DOMAINS.split(",") if d.strip()]

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_DEFAULT_MODEL: str = "llama3"

    # Default LLM provider: "openai" or "ollama"
    LLM_PROVIDER: str = "openai"

    # File storage
    UPLOAD_DIR: str = "uploads"
    MAX_AUDIO_SIZE_MB: int = 500
    MAX_VIDEO_SIZE_MB: int = 1000

    # Whisper
    WHISPER_MODEL: str = "large-v3"

    # Frontend URL
    FRONTEND_URL: str = "http://localhost:5173"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
