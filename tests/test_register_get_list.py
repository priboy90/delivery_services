# tests/test_register_get_list.py
import asyncio

import pytest


async def _wait_cost_appears(client, api_prefix, parcel_id, helpers, timeout=7.0):
    # В расширенной версии стоимость появляется почти сразу (воркер),
    # в базовой — может не появиться (тогда просто вернём None).
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        r = await client.get(f"{api_prefix}/parcels/{parcel_id}")
        if r.status_code == 200:
            item = r.json().get("data") or r.json().get("result") or r.json()
            cost = helpers["get_delivery_cost"](item)
            if cost is not None:
                return cost
        await asyncio.sleep(0.3)
    return None


@pytest.mark.asyncio
async def test_register_and_get_by_id(client, api_prefix, fx_helpers):
    # 1) Регистрируем валидную посылку
    payload = {
        "name": "Футболка",
        "weight": 0.25,
        "type_id": 1,
        "declared_usd": 20.0,
    }
    r = await client.post(f"{api_prefix}/parcels", json=payload)
    assert r.status_code in (200, 201)
    data = r.json()
    assert data.get("ok") in (True, None)  # на случай простого ответа
    parcel_id = data.get("data", {}).get("id") or data.get("id") or data.get("result", {}).get("id")
    assert parcel_id, f"в ответе нет id, ответ: {data}"

    # 2) Получаем по id, проверяем поля
    r2 = await client.get(f"{api_prefix}/parcels/{parcel_id}")
    assert r2.status_code == 200
    item = r2.json().get("data") or r2.json().get("result") or r2.json()
    assert item.get("name") == payload["name"]
    # тип либо именем, либо id
    tname = fx_helpers["get_type_name"](item)
    tid = fx_helpers["get_type_id"](item)
    assert tname or tid

    # 3) Стоимость может быть рассчитана или ещё нет
    cost = fx_helpers["get_delivery_cost"](item)
    if cost is None:
        # подождём немного — если у вас воркер её поставит
        cost = await _wait_cost_appears(client, api_prefix, parcel_id, fx_helpers)
    # теперь либо уже посчиталась, либо это базовый режим — тогда ок, что None
    assert cost is None or (isinstance(cost, float) and cost >= 0.0)


@pytest.mark.asyncio
async def test_list_pagination_and_filters(client, api_prefix, fx_helpers):
    # Создадим несколько посылок разных типов
    items = [
        {"name": "Рубашка", "weight": 0.4, "type_id": 1, "declared_usd": 30.0},
        {"name": "Телефон", "weight": 0.2, "type_id": 2, "declared_usd": 600.0},
        {"name": "Провода", "weight": 0.1, "type_id": 3, "declared_usd": 10.0},
    ]
    for it in items:
        r = await client.post(f"{api_prefix}/parcels", json=it)
        assert r.status_code in (200, 201)

    # 1) Пагинация
    r = await client.get(f"{api_prefix}/parcels?page=1&per_page=2")
    assert r.status_code == 200
    data = r.json()
    # ожидаем ключи meta/total/items в каком-то виде
    items_list = data.get("data", {}).get("items") or data.get("items") or data.get("result", {}).get("items")
    total = data.get("data", {}).get("total") or data.get("total") or data.get("result", {}).get("total")
    assert isinstance(items_list, list)
    assert len(items_list) <= 2
    assert isinstance(total, int) and total >= len(items)

    # 2) Фильтр по type_id (например, электроника==2)
    r2 = await client.get(f"{api_prefix}/parcels?type_id=2&per_page=50")
    assert r2.status_code == 200
    data2 = r2.json()
    items2 = data2.get("data", {}).get("items") or data2.get("items") or []
    assert all(fx_helpers["get_type_id"](x) in (2, None) or fx_helpers["get_type_name"](x) == "электроника" for x in items2)

    # 3) Фильтр по рассчитанной стоимости (priced=true)
    # подождём чуть-чуть, если у вас воркер, чтобы стоимость успела появиться
    await asyncio.sleep(1.0)
    r3 = await client.get(f"{api_prefix}/parcels?priced=true&per_page=50")
    assert r3.status_code == 200
    data3 = r3.json()
    items3 = data3.get("data", {}).get("items") or data3.get("items") or []
    # Допускаем, что если у вас базовый режим без моментального расчёта,
    # список может быть пуст. Но если элементы есть — у них должна быть стоимость.
    for x in items3:
        assert fx_helpers["get_delivery_cost"](x) is not None
