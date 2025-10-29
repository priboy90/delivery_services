# tests/test_session_isolation.py
import pytest


@pytest.mark.asyncio
async def test_session_isolation(client, other_client, api_prefix):
    # Клиент A создаёт посылку
    r = await client.post(
        f"{api_prefix}/parcels",
        json={
            "name": "Секретная посылка",
            "weight": 0.5,
            "type_id": 3,
            "declared_usd": 42.0,
        },
    )
    assert r.status_code in (200, 201)
    pid = r.json().get("data", {}).get("id") or r.json().get("id")
    assert pid

    # Клиент B НЕ должен видеть её в списке
    r2 = await other_client.get(f"{api_prefix}/parcels?per_page=100")
    assert r2.status_code == 200
    data = r2.json()
    items = data.get("data", {}).get("items") or data.get("items") or []
    assert all((x.get("id") != pid) for x in items)

    # И не должен получать её по id (ожидаем 404)
    r3 = await other_client.get(f"{api_prefix}/parcels/{pid}")
    assert r3.status_code in (403, 404)
