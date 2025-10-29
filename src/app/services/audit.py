# src/app/services/audit.py
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from .mongo import Mongo


async def log_parcel_calc(
    mongo: Mongo,
    *,
    session_id: str,
    parcel_id: int,
    type_id: int,
    weight_kg: Decimal,
    content_usd: Decimal,
    usd_rub: Decimal,
    cost_rub: Decimal,
    source: str,  # "sync" | "worker"
    ts: datetime | None = None,
) -> None:
    doc = {
        "ts": (ts or datetime.now(UTC)),
        "session_id": session_id,
        "parcel_id": parcel_id,
        "type_id": type_id,
        "weight_kg": str(weight_kg),
        "content_usd": str(content_usd),
        "usd_rub": str(usd_rub),
        "cost_rub": str(cost_rub),
        "source": source,
    }
    await mongo.db["calc_logs"].insert_one(doc)
