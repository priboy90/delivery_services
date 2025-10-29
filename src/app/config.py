# src/app/config.py (Python 3.12)

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field("Delivery Services", alias="APP_NAME")
    app_version: str = Field("0.1.0", alias="APP_VERSION")
    debug: bool = Field(False, alias="DEBUG")
    environment: str = Field("development", alias="ENVIRONMENT")

    api_v1_prefix: str = Field("/api/v1", alias="API_V1_STR")
    project_name: str = Field("Delivery Services API", alias="PROJECT_NAME")
    docs_url: str = Field("/docs", alias="DOCS_URL")
    redoc_url: str = Field("/redoc", alias="REDOC_URL")

    host: str = Field("0.0.0.0", alias="HOST")
    port: int = Field(8000, alias="PORT")

    session_cookie_name: str = Field("session_id", alias="SESSION_COOKIE_NAME")

    secret_key: SecretStr = Field(..., alias="SECRET_KEY")

    postgres_user: str = Field(..., alias="POSTGRES_USER")
    postgres_password: SecretStr = Field(..., alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(..., alias="POSTGRES_DB")
    postgres_host: str = Field(..., alias="POSTGRES_HOST")
    postgres_port: int = Field(..., alias="POSTGRES_PORT")

    postgres_pool_size: int = Field(20, alias="POSTGRES_POOL_SIZE")
    postgres_max_overflow: int = Field(10, alias="POSTGRES_MAX_OVERFLOW")
    postgres_pool_timeout: int = Field(30, alias="POSTGRES_POOL_TIMEOUT")
    postgres_pool_recycle: int = Field(1800, alias="POSTGRES_POOL_RECYCLE")

    postgres_dsn: str | None = Field(None, alias="POSTGRES_DSN")

    redis_url: str = Field(..., alias="REDIS_URL")
    rabbitmq_url: str = Field(..., alias="RABBITMQ_URL")

    mongodb_url: str | None = Field(None, alias="MONGODB_URL")
    mongo_url_legacy: str | None = Field(None, alias="MONGO_URL")

    # --- rate limit ---
    rate_limit_per_minute: int = Field(60, alias="RATE_LIMIT_PER_MINUTE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    @computed_field
    @property
    def effective_mongodb_url(self) -> str | None:
        return self.mongodb_url or self.mongo_url_legacy

    @computed_field
    @property
    def effective_postgres_dsn(self) -> str:
        if self.postgres_dsn:
            return self.postgres_dsn
        pwd = self.postgres_password.get_secret_value()
        return f"postgresql+asyncpg://{self.postgres_user}:{pwd}" f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if not s.mongodb_url and s.mongo_url_legacy:
        s.mongodb_url = s.mongo_url_legacy
    if not s.postgres_dsn:
        s.postgres_dsn = s.effective_postgres_dsn
    return s
