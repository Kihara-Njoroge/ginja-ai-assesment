from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    APP_NAME: str = "Ginja AI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    ALLOWED_ORIGINS: list[str] = ["*"]

    # Logging
    LOG_LEVEL: str = "INFO"

    # JWT Authentication
    SECRET_KEY: str = "default-insecure-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Google OAuth
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ginja_ai"


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
