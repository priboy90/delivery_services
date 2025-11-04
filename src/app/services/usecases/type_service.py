from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from ...repository.type_repo import TypeRepository
from ...services.mappers.type_mapper import to_public_dict


class TypeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = TypeRepository(db)

    async def list_public(self) -> list[dict]:
        rows = await self.repo.list_all()
        return [to_public_dict(r) for r in rows]
