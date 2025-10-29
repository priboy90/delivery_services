# tests/test_misc.py
import pytest


@pytest.mark.asyncio
async def test_health_and_docs(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json().get("ok") in (True, 1)

    # Swagger UI доступен
    r2 = await client.get("/docs")
    assert r2.status_code == 200
