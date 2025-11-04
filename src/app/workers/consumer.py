from __future__ import annotations

import asyncio
import logging
from decimal import Decimal
from typing import Any

import aio_pika
import orjson
import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from ..config import get_settings
from ..db.postgres import session_scope
from ..models.parcel import Parcel
from ..models.parcel_type import ParcelType
from ..services.audit import log_parcel_calc
from ..services.calc import calc_shipping
from ..services.mongo import Mongo
from ..services.rates import get_usd_rub

QUEUE_NAME = "register_parcel"
log = logging.getLogger("app.worker")


async def handle_message(body: bytes, redis, mongo: Mongo | None) -> None:
    data: dict[str, Any] = orjson.loads(body)

    required = {"session_id", "session_public_id", "name", "weight_kg", "type_id", "content_usd"}
    missing = [k for k in required if k not in data]
    if missing:
        log.error("invalid_message_missing_fields", extra={"missing": missing})
        return

    session_id = str(data["session_id"])
    session_public_id = str(data["session_public_id"])

    usd_rub = await get_usd_rub(redis)
    weight_kg = Decimal(str(data["weight_kg"]))
    content_usd = Decimal(str(data["content_usd"]))
    cost_rub = calc_shipping(weight_kg, content_usd, usd_rub)

    try:
        async with session_scope() as db:
            exists = await db.scalar(select(ParcelType.id).where(ParcelType.id == int(data["type_id"])))
            if not exists:
                log.error("unknown_type_id", extra={"type_id": data["type_id"]})
                return

            obj = Parcel(
                session_id=session_id,
                session_public_id=session_public_id,
                name=str(data["name"]),
                weight_kg=weight_kg,
                type_id=int(data["type_id"]),
                content_usd=content_usd,
                cost_rub=cost_rub,
                shipping_company_id=None,
            )
            db.add(obj)
            await db.flush()
            parcel_id = obj.id
    except IntegrityError:
        log.warning("duplicate_message_ignored", extra={"session_id": session_id, "public_id": session_public_id})
        return

    if mongo is not None:
        try:
            await log_parcel_calc(
                mongo,
                session_id=session_id,
                parcel_id=parcel_id,
                type_id=int(data["type_id"]),
                weight_kg=weight_kg,
                content_usd=content_usd,
                usd_rub=usd_rub,
                cost_rub=cost_rub,
                source="worker",
            )
        except Exception:
            log.exception("audit_log_failed")

    log.info("parcel_registered", extra={"name": data["name"], "type_id": data["type_id"]})


async def main() -> None:
    s = get_settings()
    logging.basicConfig(level=logging.INFO)
    log.info("worker_starting")

    redis = aioredis.from_url(s.redis_url, decode_responses=True)

    mongo: Mongo | None = None
    if s.mongodb_url:
        mongo = Mongo(s.mongodb_url, db_name="delivery")
        try:
            await mongo.connect()
        except Exception:
            mongo = None
            log.exception("mongo_connect_failed")

    connection = await aio_pika.connect_robust(s.rabbitmq_url)
    try:
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(QUEUE_NAME, durable=True)

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process(ignore_processed=True, requeue=False):
                        try:
                            await handle_message(message.body, redis, mongo)
                        except Exception:
                            log.exception("message_processing_failed")
    finally:
        try:
            await redis.aclose()
        except Exception:
            pass
        if mongo is not None:
            try:
                await mongo.close()
            except Exception:
                pass
        log.info("worker_stopped")


if __name__ == "__main__":
    asyncio.run(main())
