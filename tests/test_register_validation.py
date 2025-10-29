# tests/test_register_validation.py
import pytest


@pytest.mark.asyncio
async def test_register_requires_json_and_validation(client, api_prefix):
    # Пустое тело → 422
    r = await client.post(f"{api_prefix}/parcels", json={})
    assert r.status_code in (400, 422)
    data = r.json()
    # у вас централизованный обработчик -> code == "validation_error"
    assert isinstance(data, dict)
    assert data.get("ok") is False
    err_code = data.get("code") or data.get("error") or ""
    assert "validation" in err_code


@pytest.mark.asyncio
async def test_register_negative_weight_fails(client, api_prefix):
    bad = {
        "name": "Тяжелая вещь",
        "weight": -1.0,  # некорректно
        "type_id": 1,
        "declared_usd": 100.0,
    }
    r = await client.post(f"{api_prefix}/parcels", json=bad)
    assert r.status_code in (400, 422)
