from __future__ import annotations

from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

import httpx
from fastapi import Request
from redis.asyncio import Redis

DEFAULT_USD_RUB = Decimal("100.00")
CACHE_KEY = "usd_rub"
CACHE_TTL_SECONDS = int(timedelta(hours=3).total_seconds())


async def _fetch_usd_rub_from_cbr(timeout: float = 3.0) -> Decimal | None:
    """
    Берём актуальный курс доллара к рублю из ЦБ РФ.
    Источник: https://www.cbr-xml-daily.ru/daily_json.js
    Возвращаем Decimal с округлением до копеек.
    """
    url = "https://www.cbr-xml-daily.ru/daily_json.js"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
            val = data["Valute"]["USD"]["Value"]
            # подстрахуемся на типы
            value = Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            return value
    except Exception:
        return None


async def get_usd_rub(redis: Redis | None) -> Decimal:
    """
    Пытаемся получить курс из Redis; при промахе — запрашиваем ЦБ, кладём в кэш.
    Возвращаем Decimal с двумя знаками.
    """
    if redis:
        try:
            raw = await redis.get(CACHE_KEY)
            if raw:
                return Decimal(str(raw)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except Exception:
            pass

    fetched = await _fetch_usd_rub_from_cbr()
    if fetched is None:
        fetched = DEFAULT_USD_RUB

    if redis:
        try:
            await redis.setex(CACHE_KEY, CACHE_TTL_SECONDS, str(fetched))
        except Exception:
            pass

    return fetched


def get_redis_from_request(request: Request) -> Redis | None:
    """
    Возвращает Redis-инстанс из app.state.redis, если он инициализирован в lifespan.
    """
    return getattr(request.app.state, "redis", None)
