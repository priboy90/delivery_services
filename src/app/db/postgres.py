# FILE: src/app/db/postgres.py
# PLACE: замените целиком содержимое файла

"""
Асинхронная обвязка PostgreSQL для SQLAlchemy 2.x:
- get_engine() — лениво создаёт AsyncEngine
- get_session_factory() — sessionmaker для AsyncSession
- get_session() — зависимость FastAPI
- session_scope() — контекст-менеджер транзакции
- create_schema() — создание схемы (Alembic отдельно)
Поддерживает DATABASE_URL или POSTGRES_* переменные окружения.

Дополнительно:
- redact_dsn() — маскирование пароля в DSN для логов
- reset_connections_for_tests() — аккуратный сброс движка/фабрики для юнит-тестов
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

# Чтобы не создавать движок многократно:
_engine: AsyncEngine | None = None
_SessionFactory: sessionmaker | None = None

log = logging.getLogger("app.db")


def _build_database_url() -> str:
    """
    Возвращает DSN для asyncpg.

    Приоритет:
      1) DATABASE_URL (например: postgresql+asyncpg://user:pass@host:5432/db)
      2) POSTGRES_USER/POSTGRES_PASSWORD/POSTGRES_HOST/POSTGRES_PORT/POSTGRES_DB
    """
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "postgres")

    # ВАЖНО: драйвер async — postgresql+asyncpg
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


def _redact_dsn(dsn: str) -> str:
    """
    Маскирует пароль в DSN для логирования.
    postgresql+asyncpg://user:***@host:port/db
    """
    try:
        # грубая, но быстрая маскировка; без лишних зависимостей
        if "://" not in dsn or "@" not in dsn:
            return dsn
        prefix, rest = dsn.split("://", 1)
        creds, tail = rest.split("@", 1)
        if ":" in creds:
            user, _pwd = creds.split(":", 1)
            creds_redacted = f"{user}:***"
        else:
            creds_redacted = creds
        return f"{prefix}://{creds_redacted}@{tail}"
    except Exception:
        return dsn


def get_engine(echo: bool | None = None) -> AsyncEngine:
    """
    Ленивая инициализация движка.
    echo можно включить через переменную окружения SQL_ECHO=1 для отладки.
    """
    global _engine
    if _engine is None:
        url = _build_database_url()
        if echo is None:
            echo = os.getenv("SQL_ECHO", "0") == "1"
        _engine = create_async_engine(url, echo=echo, pool_pre_ping=True)
        # Не палим пароль в логах
        log.info("Async engine created %s", _redact_dsn(url))
    return _engine


def get_session_factory() -> sessionmaker:
    """
    Возвращает sessionmaker, привязанный к AsyncEngine.
    """
    global _SessionFactory
    if _SessionFactory is None:
        engine = get_engine()
        _SessionFactory = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    return _SessionFactory


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    """
    Контекст-менеджер транзакции:
        async with session_scope() as session:
            ...
    """
    Session = get_session_factory()
    session: AsyncSession = Session()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость FastAPI:
        async def endpoint(db: AsyncSession = Depends(get_session)):
            ...
    """
    Session = get_session_factory()
    async with Session() as session:
        yield session


async def create_schema() -> None:
    """
    Создание схемы по декларативным моделям.
    В проде обычно используется Alembic, но для unit-тестов удобно.
    """
    from ..db.base import Base  # локальный импорт, чтобы избежать циклов

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Database schema ensured")


async def reset_connections_for_tests() -> None:
    """
    Полезно в тестах:
    - закрыть и обнулить текущий AsyncEngine
    - обнулить фабрику сессий
    Вызывай в фикстуре pytest между сценариями, если меняешь DATABASE_URL.
    """
    global _engine, _SessionFactory
    if _SessionFactory is not None:
        _SessionFactory = None
    if _engine is not None:
        try:
            await _engine.dispose()
        finally:
            _engine = None
