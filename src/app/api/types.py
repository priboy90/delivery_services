from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.postgres import get_session
from ..services.usecases.type_service import TypeService
from .responses import ok

router = APIRouter()


@router.get("/parcel-types")
async def list_parcel_types(db: Annotated[AsyncSession, Depends(get_session)]):
    """
    Базовый маршрут получения типов: /parcel-types
    """
    svc = TypeService(db)
    return ok(await svc.list_public())


@router.get("/types")
async def list_types_alias(db: Annotated[AsyncSession, Depends(get_session)]):
    """
    Совместимый алиас под тесты:
    """
    svc = TypeService(db)
    return ok(await svc.list_public())
