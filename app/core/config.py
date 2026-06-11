import json
import os
from enum import StrEnum
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Environment(StrEnum):
    PROD = "prod"
    STAGE = "stage"
    DEV = "dev"
    TEST = "test"


def _env_files() -> list[str]:
    environment = os.getenv("ENV", "dev")
    candidates = [PROJECT_ROOT / ".env", PROJECT_ROOT / f".env.{environment}"]
    return [str(path) for path in candidates if path.exists()]


class Settings(BaseSettings):
    APP_NAME: str = "FastAPI Auth Telegram Base"
    PROJECT_NAME: str = "anno-bot-be"
    ENV: Environment = Environment.DEV
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite+pysqlite:///./app.db"

    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    BACKEND_CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])
    FRONTEND_URL: str = "http://localhost:3000"

    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_BOT_USERNAME: str | None = None
    TELEGRAM_BOT_API_BASE_URL: str = "https://api.telegram.org"
    TELEGRAM_AUTH_MAX_AGE_SECONDS: int = 60 * 60 * 24
    TELEGRAM_LINK_TOKEN_EXPIRE_MINUTES: int = 10
    TELEGRAM_WEBHOOK_SECRET_TOKEN: str | None = None
    TELEGRAM_LOGIN_CLIENT_ID: str | None = None
    TELEGRAM_LOGIN_CLIENT_SECRET: str | None = None
    TELEGRAM_OIDC_ISSUER: str = "https://oauth.telegram.org"
    TELEGRAM_OIDC_JWKS_URL: str = "https://oauth.telegram.org/.well-known/jwks.json"
    TELEGRAM_OIDC_TOKEN_URL: str = "https://oauth.telegram.org/token"
    TELEGRAM_OIDC_CLOCK_SKEW_SECONDS: int = 60

    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    OPIK_PROJECT_NAME: str = "anno_bot"

    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                return list(json.loads(stripped))
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def DATABASE_URI(self) -> str:
        return self.DATABASE_URL

    @property
    def is_production(self) -> bool:
        return self.ENV == Environment.PROD


settings = Settings()
