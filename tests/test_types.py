# tests/test_types.py
import pytest


@pytest.mark.asyncio
async def test_get_types(client, api_prefix):
    r = await client.get(f"{api_prefix}/types")
    assert r.status_code == 200
    data = r.json()
    # Ожидаем стандартизованный ответ: ok: true и payload
    assert isinstance(data, dict)
    assert data.get("ok") is True
    items = data.get("data") or data.get("result") or data.get("items") or data.get("payload")
    assert isinstance(items, list)

    names = {(i.get("id"), (i.get("name") or i.get("title") or i.get("label") or "").lower()) for i in items}
    # Должны быть 3 типа
    assert any(name == "одежда" for _, name in names)
    assert any(name == "электроника" for _, name in names)
    assert any(name == "разное" for _, name in names)
