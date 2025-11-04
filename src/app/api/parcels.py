from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, Field, condecimal, constr
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.responses import ok
from ..api.utils import ensure_session_id
from ..config import get_settings
from ..db.postgres import get_session
from ..schemas.pagination import Page
from ..schemas.parcel import ParcelOut
from ..schemas.parcel_compat import ParcelCompatOut, ParcelRegisterCompatIn
from ..services.mappers.parcel_mapper import to_public_dict
from ..services.usecases.parcel_service import ParcelService

router = APIRouter(prefix="/parcels", tags=["parcels"])


class ParcelRegisterIn(BaseModel):
    name: constr(min_length=1, max_length=300)
    weight_kg: condecimal(gt=Decimal("0"), max_digits=10, decimal_places=3)
    type_id: int = Field(gt=0)
    content_usd: condecimal(ge=Decimal("0"), max_digits=12, decimal_places=2)


@router.post("/register", status_code=status.HTTP_202_ACCEPTED)
async def register_parcel(request: Request, data: ParcelRegisterIn, db: Annotated[AsyncSession, Depends(get_session)]):
    session_id = ensure_session_id(request)
    s = get_settings()
    svc = ParcelService(db)
    public_id = await svc.register_async(
        request=request,
        session_id=session_id,
        name=data.name,
        weight_kg=Decimal(str(data.weight_kg)),
        type_id=data.type_id,
        content_usd=Decimal(str(data.content_usd)),
        rabbitmq_url=s.rabbitmq_url,
    )
    return ok({"public_id": public_id})


@router.post("/register-sync", status_code=status.HTTP_201_CREATED)
async def register_parcel_sync(
    request: Request,
    data: ParcelRegisterIn,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    session_id = ensure_session_id(request)
    svc = ParcelService(db)
    obj = await svc.register_sync(
        request=request,
        session_id=session_id,
        name=data.name,
        weight_kg=Decimal(str(data.weight_kg)),
        type_id=data.type_id,
        content_usd=Decimal(str(data.content_usd)),
        mongo=getattr(request.app.state, "mongo", None),
    )
    # совместимый ответ (как было)
    return ok(
        {
            "id": obj.id,
            "public_id": obj.session_public_id,
            "name": obj.name,
            "weight_kg": str(obj.weight_kg),
            "type_id": obj.type_id,
            "content_usd": str(obj.content_usd),
            "cost_rub": (str(obj.cost_rub) if obj.cost_rub is not None else None),
        }
    )


@router.get("", response_model=Page[ParcelOut])
async def list_parcels(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    type_id: int | None = Query(None, description="Фильтр по типу"),
    has_cost: bool | None = Query(None, description="Фильтр по факту наличия рассчитанной стоимости"),
    priced: bool | None = Query(None, description="Алиас has_cost"),
):
    session_id = ensure_session_id(request)
    if has_cost is None and priced is not None:
        has_cost = priced
    svc = ParcelService(db)
    total, rows = await svc.list(session_id=session_id, page=page, per_page=per_page, type_id=type_id, has_cost=has_cost)
    items = [ParcelOut(**to_public_dict(prc, ptype_name)) for prc, ptype_name in rows]
    return Page(items=items, page=page, per_page=per_page, total=total)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ParcelCompatOut)
async def register_parcel_compat(
    request: Request,
    data: ParcelRegisterCompatIn,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    session_id = ensure_session_id(request)
    svc = ParcelService(db)
    obj = await svc.register_sync(
        request=request,
        session_id=session_id,
        name=data.name,
        weight_kg=Decimal(str(data.weight)),
        type_id=data.type_id,
        content_usd=Decimal(str(data.declared_usd)),
        mongo=getattr(request.app.state, "mongo", None),
    )
    return ParcelCompatOut(
        id=obj.id,
        name=obj.name,
        type_id=obj.type_id,
        type_name="",
        weight=obj.weight_kg,
        content_usd=obj.content_usd,
        cost_rub=obj.cost_rub,
    )


@router.get("/id/{item_id}", response_model=ParcelCompatOut)
async def get_parcel_by_numeric_id(
    item_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    session_id = ensure_session_id(request)
    svc = ParcelService(db)
    prc, ptype_name = await svc.get_by_id(session_id=session_id, item_id=item_id)
    return ParcelCompatOut(
        id=prc.id,
        name=prc.name,
        type_id=prc.type_id,
        type_name=ptype_name,
        weight=prc.weight_kg,
        content_usd=prc.content_usd,
        cost_rub=prc.cost_rub,
    )


@router.get("/public/{public_id}", response_model=ParcelOut)
async def get_parcel(
    public_id: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    session_id = ensure_session_id(request)
    svc = ParcelService(db)
    prc, ptype_name = await svc.get_by_public(session_id=session_id, public_id=public_id)
    return ParcelOut(**to_public_dict(prc, ptype_name))


@router.post("/public/{public_id}/bind", status_code=status.HTTP_200_OK)
async def bind_parcel_to_company(
    public_id: str,
    company_id: Annotated[int, Query(gt=0)],
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    session_id = ensure_session_id(request)
    svc = ParcelService(db)
    ok_result = await svc.bind_company(session_id=session_id, public_id=public_id, company_id=company_id)
    return ok(ok_result)
