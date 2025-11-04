from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.parcel import Parcel
from ...repository.parcel_repo import ParcelRepository
from ...services.audit import log_parcel_calc
from ...services.calc import calc_shipping
from ...services.mongo import Mongo
from ...services.mq_producer import send_register_message
from ...services.rates import get_redis_from_request, get_usd_rub


class ParcelService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ParcelRepository(db)

    async def register_async(self, *, request, session_id: str, name: str, weight_kg: Decimal, type_id: int, content_usd: Decimal, rabbitmq_url: str) -> str:
        public_id = uuid.uuid4().hex
        payload = {
            "session_id": session_id,
            "session_public_id": public_id,
            "name": name,
            "weight_kg": str(weight_kg),
            "type_id": type_id,
            "content_usd": str(content_usd),
        }
        await send_register_message(rabbitmq_url, payload)
        return public_id

    async def register_sync(self, *, request, session_id: str, name: str, weight_kg: Decimal, type_id: int, content_usd: Decimal, mongo: Mongo | None = None) -> Parcel:
        if not await self.repo.exists_type(type_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown type_id")

        redis = get_redis_from_request(request)
        usd_rub = await get_usd_rub(redis)

        obj = Parcel(
            session_id=session_id,
            session_public_id=uuid.uuid4().hex,
            name=name,
            weight_kg=Decimal(str(weight_kg)),
            type_id=type_id,
            content_usd=Decimal(str(content_usd)),
            cost_rub=calc_shipping(Decimal(str(weight_kg)), Decimal(str(content_usd)), usd_rub),
        )
        obj = await self.repo.create(obj)
        await self.db.commit()

        if mongo is not None:
            try:
                await log_parcel_calc(
                    mongo,
                    session_id=session_id,
                    parcel_id=obj.id,
                    type_id=type_id,
                    weight_kg=obj.weight_kg,
                    content_usd=obj.content_usd,
                    usd_rub=usd_rub,
                    cost_rub=obj.cost_rub,  # type: ignore[arg-type]
                    source="sync",
                )
            except Exception:
                # не роняем запрос из-за сбоя аудита
                pass

        return obj

    async def list(self, *, session_id: str, page: int, per_page: int, type_id: int | None, has_cost: bool | None):
        return await self.repo.paginate(session_id, page, per_page, type_id=type_id, has_cost=has_cost)

    async def get_by_id(self, *, session_id: str, item_id: int):
        row = await self.repo.get_by_id_in_session(session_id, item_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found")
        return row

    async def get_by_public(self, *, session_id: str, public_id: str):
        row = await self.repo.get_by_public_in_session(session_id, public_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcel not found")
        return row

    async def bind_company(self, *, session_id: str, public_id: str, company_id: int):
        changed = await self.repo.bind_first_wins(session_id, public_id, company_id)
        if changed == 0:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already bound or not found")
        await self.db.commit()
        return True
