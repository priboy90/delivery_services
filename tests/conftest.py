import os

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from src.app.db.postgres import reset_connections_for_tests
from src.app.main import create_app


@pytest.fixture
async def app() -> FastAPI:
    """
    ВАЖНО: function-scope, чтобы у каждого теста был свой event loop
    и свой fresh AsyncEngine/пул соединений.
    После теста — аккуратноDispose/обнуляем движок.
    """
    app = create_app()
    try:
        yield app
    finally:
        await reset_connections_for_tests()


@pytest.fixture
async def client(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def other_client(app: FastAPI):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


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
        if k not in obj:
            continue
        v = obj.get(k)
        if v is None:
            continue
        if isinstance(v, str) and "не рассчит" in v.lower():
            continue
        try:
            return float(v)
        except Exception:
            continue
    return None


@pytest.fixture
def api_prefix() -> str:
    return os.getenv("API_PREFIX", "/api/v1")


@pytest.fixture
def fx_helpers():
    return {
        "get_type_name": _get_type_name,
        "get_type_id": _get_type_id,
        "get_delivery_cost": _get_delivery_cost,
    }
