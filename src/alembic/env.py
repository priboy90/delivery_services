# alembic/env.py

from __future__ import annotations

import asyncio
import importlib
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from src.app.models.base import Base  # target_metadata

from alembic import context

# -----------------------------------------------------------------------------
# Alembic Config
# -----------------------------------------------------------------------------
config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


importlib.import_module("src.app.models.parcel")
importlib.import_module("src.app.models.parcel_type")


target_metadata = Base.metadata


# -----------------------------------------------------------------------------
# Offline migrations
# -----------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """Запуск миграций в offline-режиме (без подключения к БД)."""
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("В alembic.ini не задан sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=False,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# -----------------------------------------------------------------------------
# Online migrations
# -----------------------------------------------------------------------------
def do_run_migrations(connection) -> None:
    """Синхронная часть, которую Alembic вызывает внутри run_sync."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Запуск миграций в online-режиме (с подключением к БД)."""
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("В alembic.ini не задан sqlalchemy.url")

    engine = create_async_engine(url, poolclass=pool.NullPool)

    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await engine.dispose()


# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
