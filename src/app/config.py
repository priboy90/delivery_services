from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Delivery Services"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    api_v1_prefix: str = "/api/v1"
    project_name: str = "Delivery Services API"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"

    host: str = "0.0.0.0"
    port: int = 8000

    session_cookie_name: str = "session_id"
    secret_key: SecretStr

    postgres_user: str
    postgres_password: SecretStr
    postgres_db: str
    postgres_host: str
    postgres_port: int

    postgres_pool_size: int = 20
    postgres_max_overflow: int = 10
    postgres_pool_timeout: int = 30
    postgres_pool_recycle: int = 1800

    postgres_dsn: str | None = None

    redis_url: str
    rabbitmq_url: str

    mongodb_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("MONGODB_URL", "MONGO_URL"),
    )

    rate_limit_per_minute: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    @computed_field
    @property
    def effective_mongodb_url(self) -> str | None:
        return self.mongodb_url

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
    if not s.postgres_dsn:
        s.postgres_dsn = s.effective_postgres_dsn
    return s
