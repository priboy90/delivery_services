from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

import aio_pika
import orjson

QUEUE_NAME = "register_parcel"


async def send_register_message(amqp_url: str, payload: Mapping[str, Any]) -> None:
    """
    Публикует сообщение в очередь регистрации посылки.
    Ожидается, что payload уже содержит `session_public_id`.
    Сообщение делаем durable (persistent).
    """
    connection = await aio_pika.connect_robust(amqp_url)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        msg = aio_pika.Message(
            body=orjson.dumps(payload),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
            type="register_parcel",
        )
        await channel.default_exchange.publish(msg, routing_key=queue.name)


if __name__ == "__main__":

    async def _main():
        import os

        url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        sample = {
            "client_request_id": "debug",
            "session_id": "debug-session",
            "session_public_id": "deadbeefdeadbeefdeadbeefdeadbeef",
            "name": "Test",
            "weight_kg": "1.0",
            "type_id": 1,
            "content_usd": "100.00",
        }
        await send_register_message(url, sample)

    asyncio.run(_main())
