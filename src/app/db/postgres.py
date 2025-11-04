"""
Асинхронная обвязка PostgreSQL для SQLAlchemy 2.x:
- get_engine() — лениво создаёт AsyncEngine c параметрами пула из настроек
- get_session_factory() — sessionmaker для AsyncSession
- get_session() — зависимость FastAPI
- session_scope() — контекст-менеджер транзакции
- create_schema() — создание схемы (Alembic отдельно)
- reset_connections_for_tests() — аккуратный сброс движка/фабрики для юнит-тестов
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from ..config import get_settings

_engine: AsyncEngine | None = None
_SessionFactory: sessionmaker | None = None

log = logging.getLogger("app.db")


def _choose_database_url() -> str:
    """
    Приоритет выбора DSN:
      1) DATABASE_URL (например: postgresql+asyncpg://user:pass@host:5432/db)
      2) Settings.postgres_dsn (собирается из POSTGRES_* в get_settings)
    """
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    s = get_settings()
    # get_settings() уже проставляет s.postgres_dsn, при необходимости собирая его
    return s.postgres_dsn  # type: ignore[return-value]


def _redact_dsn(dsn: str) -> str:
    """
    Маскирует пароль в DSN для логирования.
    postgresql+asyncpg://user:***@host:port/db
    """
    try:
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
    Ленивая инициализация AsyncEngine c параметрами пула из настроек.
    echo можно включить через переменную окружения SQL_ECHO=1 для отладки.
    """
    global _engine
    if _engine is None:
        s = get_settings()
        url = _choose_database_url()
        if echo is None:
            echo = os.getenv("SQL_ECHO", "0") == "1"

        # Подхватываем параметры пула из настроек (замечание ревьюера)
        _engine = create_async_engine(
            url,
            echo=echo,
            pool_pre_ping=True,
            pool_size=s.postgres_pool_size,
            max_overflow=s.postgres_max_overflow,
            pool_recycle=s.postgres_pool_recycle,
            pool_timeout=s.postgres_pool_timeout,
        )
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
    Вызывай в фикстуре pytest между сценариями, если меняешь DATABASE_URL/loop.
    """
    global _engine, _SessionFactory
    if _SessionFactory is not None:
        _SessionFactory = None
    if _engine is not None:
        try:
            await _engine.dispose()
        finally:
            _engine = None
