from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.parcel import Parcel
from ..models.parcel_type import ParcelType


class ParcelRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def exists_type(self, type_id: int) -> bool:
        q = select(ParcelType.id).where(ParcelType.id == type_id).limit(1)
        return (await self.db.scalar(q)) is not None

    async def create(self, obj: Parcel) -> Parcel:
        self.db.add(obj)
        await self.db.flush()
        return obj

    async def get_by_id_in_session(self, session_id: str, item_id: int) -> tuple[Parcel, str] | None:
        q = select(Parcel, ParcelType.name).join(ParcelType, ParcelType.id == Parcel.type_id).where(and_(Parcel.session_id == session_id, Parcel.id == item_id)).limit(1)
        return (await self.db.execute(q)).first()

    async def get_by_public_in_session(self, session_id: str, public_id: str) -> tuple[Parcel, str] | None:
        q = select(Parcel, ParcelType.name).join(ParcelType, ParcelType.id == Parcel.type_id).where(and_(Parcel.session_id == session_id, Parcel.session_public_id == public_id)).limit(1)
        return (await self.db.execute(q)).first()

    async def paginate(self, session_id: str, page: int, per_page: int, *, type_id: int | None, has_cost: bool | None) -> tuple[int, list[tuple[Parcel, str]]]:
        where = [Parcel.session_id == session_id]
        if type_id is not None:
            where.append(Parcel.type_id == type_id)
        if has_cost is not None:
            where.append(Parcel.cost_rub.is_not(None) if has_cost else Parcel.cost_rub.is_(None))

        total = await self.db.scalar(select(func.count()).select_from(select(Parcel.id).where(*where).subquery())) or 0

        q = select(Parcel, ParcelType.name).join(ParcelType, ParcelType.id == Parcel.type_id).where(*where).order_by(Parcel.id.desc()).offset((page - 1) * per_page).limit(per_page)
        rows: Iterable[tuple[Parcel, str]] = (await self.db.execute(q)).all()
        return int(total), list(rows)

    async def bind_first_wins(self, session_id: str, public_id: str, company_id: int) -> int:
        stmt = (
            update(Parcel)
            .where(
                and_(
                    Parcel.session_id == session_id,
                    Parcel.session_public_id == public_id,
                    Parcel.shipping_company_id.is_(None),
                )
            )
            .values(shipping_company_id=company_id)
            .execution_options(synchronize_session=False)
        )
        res = await self.db.execute(stmt)
        return res.rowcount or 0
