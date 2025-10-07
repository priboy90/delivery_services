# src/core/models.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from .settings import settings

# Асинхронный engine с оптимизированными настройками пула
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DB_ECHO,
    future=True,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=settings.POSTGRES_POOL_SIZE,
    max_overflow=settings.POSTGRES_MAX_OVERFLOW,
    pool_timeout=settings.POSTGRES_POOL_TIMEOUT,
    pool_recycle=settings.POSTGRES_POOL_RECYCLE,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
)

# Асинхронная фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронная зависимость для получения сессии базы данных"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()