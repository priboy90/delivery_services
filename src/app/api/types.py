# FILE: src/app/api/types.py
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.parcel_type import ParcelType
from .deps import get_db
from .responses import ok

router = APIRouter()


@router.get("/parcel-types")
async def list_parcel_types(db: Annotated[AsyncSession, Depends(get_db)]):
    """
    Базовый маршрут получения типов: /parcel-types
    """
    stmt = select(ParcelType).order_by(ParcelType.id.asc())
    rows = (await db.execute(stmt)).scalars().all()
    data = [{"id": r.id, "name": r.name} for r in rows]
    return ok(data)


@router.get("/types")
async def list_types_alias(db: Annotated[AsyncSession, Depends(get_db)]):
    """
    Совместимый алиас под тесты:
    """
    stmt = select(ParcelType).order_by(ParcelType.id.asc())
    rows = (await db.execute(stmt)).scalars().all()
    data = [{"id": r.id, "name": r.name} for r in rows]
    return ok(data)
