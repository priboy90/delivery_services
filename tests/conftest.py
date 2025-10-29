# tests/conftest.py
import asyncio
import os

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

# ВАЖНО: импортируем именно ваше приложение
# Если у вас другое место — поправьте импорт.
from src.app.main import create_app


# Нужен event loop уровня session, чтобы не пересоздавался между тестами
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def app() -> FastAPI:
    # Используем реальный lifespan (БД, Redis, Mongo и т.д.)
    return create_app()


@pytest.fixture
async def client(app: FastAPI):
    # httpx AsyncClient c ASGI-приложением.
    # cookies сохраняются, значит одна "сессия" на фикстуру.
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def other_client(app: FastAPI):
    # Вторая независимая сессия (другие cookies)
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# Утилиты для гибкого доступа к полям — на случай, если имена чуть отличаются.


def _get_type_name(obj: dict) -> str | None:
    for k in ("type_name", "parcel_type_name", "type"):
        v = obj.get(k)
        if isinstance(v, str):
            return v
    return None


def _get_type_id(obj: dict) -> int | None:
    for k in ("type_id", "parcel_type_id"):
        v = obj.get(k)
        if isinstance(v, int):
            return v
    return None


def _get_delivery_cost(obj: dict) -> float | None:
    for k in ("delivery_cost_rub", "delivery_cost", "cost_rub"):
        v = obj.get(k)
        if v is None:
            return None
        # строка "Не рассчитано" — трактуем как None
        if isinstance(v, str) and "не рассчит" in v.lower():
            return None
        try:
            return float(v)
        except Exception:
            return None


@pytest.fixture
def api_prefix() -> str:
    # По умолчанию в коде s.api_v1_prefix == "/api/v1"
    # Если у вас переопределено — можно выставить переменную окружения
    return os.getenv("API_PREFIX", "/api/v1")


@pytest.fixture
def fx_helpers():
    return {
        "get_type_name": _get_type_name,
        "get_type_id": _get_type_id,
        "get_delivery_cost": _get_delivery_cost,
    }
