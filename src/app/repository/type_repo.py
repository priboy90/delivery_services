from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.parcel_type import ParcelType


class TypeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self) -> list[ParcelType]:
        stmt = select(ParcelType).order_by(ParcelType.id.asc())
        return (await self.db.execute(stmt)).scalars().all()
