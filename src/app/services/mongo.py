# src/app/services/mongo.py
from __future__ import annotations

from fastapi import Request
from motor.motor_asyncio import AsyncIOMotorClient


class Mongo:
    def __init__(self, url: str, db_name: str = "delivery"):
        self._client: AsyncIOMotorClient | None = None
        self._db_name = db_name
        self._url = url

    async def connect(self):
        self._client = AsyncIOMotorClient(self._url)
        # ленивая проверка соединения
        await self.client.admin.command("ping")
        # индексы для коллекции логов
        await self.db["calc_logs"].create_index([("ts", 1)])
        await self.db["calc_logs"].create_index([("session_id", 1), ("ts", -1)])

    async def close(self):
        if self._client is not None:
            self._client.close()
            self._client = None

    @property
    def client(self) -> AsyncIOMotorClient:
        assert self._client is not None, "Mongo is not connected"
        return self._client

    @property
    def db(self):
        return self.client[self._db_name]


async def get_mongo_from_request(request: Request) -> Mongo | None:
    """
    FastAPI-зависимость: возвращает Mongo, если настроен в app.state.mongo, иначе None.
    """
    return getattr(request.app.state, "mongo", None)
