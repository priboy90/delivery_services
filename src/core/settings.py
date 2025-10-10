# src/core/settings.py
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, validator
from typing import Optional, List, Any, Dict
import os


class Settings(BaseSettings):
    """Настройки асинхронного приложения"""

    # Базовые настройки
    APP_NAME: str
    APP_VERSION: str
    DEBUG: bool
    ENVIRONMENT: str

    # Настройки API
    API_V1_STR: str
    PROJECT_NAME: str
    DOCS_URL: str
    REDOC_URL: str

    # Настройки сервера
    HOST: str
    PORT: int
    RELOAD: bool

    # Настройки CORS
    CORS_ORIGINS: str

    validator("CORS_ORIGINS", pre=True)

    def parse_cors_origins(cls, v: str) -> List[str]:
        """Преобразует строку с перечислением origin'ов в список"""
        if isinstance(v, list):
            return v
        return [origin.strip() for origin in v.split(",")]

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        validate_assignment = True

    # Настройки базы данных (асинхронные)
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_PORT: int
    POSTGRES_POOL_SIZE: int
    POSTGRES_MAX_OVERFLOW: int
    POSTGRES_POOL_TIMEOUT: int
    POSTGRES_POOL_RECYCLE: int

    # Async Database URL для asyncpg
    DATABASE_URL: Optional[PostgresDsn] = None

    # Настройки логирования
    LOG_LEVEL: str

    @validator("DATABASE_URL", pre=True)
    def assemble_async_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """Собирает асинхронный URL для подключения к базе данных"""
        # что вернет подробно
        if isinstance(v, str):
            return v

        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"{values.get('POSTGRES_DB') or ''}",
        )

    # Sync Database URL только для Alembic
    SYNC_DATABASE_URL: Optional[PostgresDsn] = None

    @validator("SYNC_DATABASE_URL", pre=True)
    def assemble_sync_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        """Собирает синхронный URL для миграций Alembic"""
        if isinstance(v, str):
            return v

        return PostgresDsn.build(
            scheme="postgresql+psycopg2",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=values.get("POSTGRES_PORT"),
            path=f"{values.get('POSTGRES_DB', '')}",
        )

    # Настройки асинхронного пула соединений
    DB_ECHO: bool
    DB_POOL_PRE_PING: bool

    # Настройки безопасности
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Настройки логирования
    LOG_LEVEL: str
    LOG_FORMAT: str

    # Настройки лимитов запросов
    RATE_LIMIT_PER_MINUTE: int

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
        validate_assignment = True

    # Настройки сессий
    SECRET_KEY : str
    SESSION_COOKIE_NAME : str

# Глобальный экземпляр настроек
settings = Settings()