"""Application settings loaded from environment variables."""

import json
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Validated runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        enable_decoding=False,
    )

    database_url: str | None = Field(default=None, validation_alias="DATABASE_URL")
    db_host: str = "127.0.0.1"
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_name: str = "subastagro_db"
    db_user: str = "postgres"
    db_password: str = ""
    secret_key: str = Field(validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET"))
    algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(
        default=30,
        gt=0,
        validation_alias=AliasChoices(
            "ACCESS_TOKEN_EXPIRE_MINUTES", "ACCESS_TOKEN_MINUTES"
        ),
    )
    refresh_token_expire_days: int = Field(default=7, gt=0)
    environment: Literal["development", "test", "production"] = "development"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"]
    )
    cookie_name: str = "subastagro_refresh"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        """Accept JSON arrays or comma-separated origin lists."""
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                return json.loads(stripped)
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        """Reject secrets too short for HMAC signing."""
        if len(value) < 32:
            raise ValueError("SECRET_KEY must contain at least 32 characters")
        return value

    @model_validator(mode="after")
    def require_database_credentials(self) -> "Settings":
        if not self.database_url and not self.db_password:
            raise ValueError(
                "Define DATABASE_URL o DB_PASSWORD para conectar a PostgreSQL"
            )
        return self

    @property
    def sqlalchemy_database_url(self) -> str:
        """Return the configured PostgreSQL connection URL."""
        if self.database_url:
            return self.database_url
        return URL.create(
            "postgresql+psycopg2",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        ).render_as_string(hide_password=False)


settings = Settings()
