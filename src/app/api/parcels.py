# src/app/api/parcels.py (replace whole file)

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, condecimal, constr
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.responses import ok
from ..config import get_settings
from ..db.postgres import get_session
from ..models.parcel import Parcel
from ..models.parcel_type import ParcelType
from ..services.mq_producer import send_register_message
from ..services.rates import get_usd_rub

router = APIRouter()


# -----------------------------
# Schemas
# -----------------------------
class ParcelRegisterIn(BaseModel):
    name: constr(min_length=1, max_length=300)
    weight_kg: condecimal(gt=Decimal("0"), max_digits=10, decimal_places=3)
    type_id: int = Field(gt=0)
    content_usd: condecimal(ge=Decimal("0"), max_digits=12, decimal_places=2)


class ParcelOut(BaseModel):
    id: int
    session_public_id: str = Field(serialization_alias="public_id")
    name: str
    weight_kg: Decimal
    type_id: int
    type_name: str
    content_usd: Decimal
    cost_rub: Decimal | None
    delivery_cost_rub: Decimal | None = None
    shipping_company_id: int | None
    model_config = {"populate_by_name": True}


class Page(BaseModel):
    items: list[ParcelOut]
    page: int
    per_page: int
    total: int


# -----------------------------
# Helpers
# -----------------------------
def get_session_id(request: Request) -> str:
    sid = getattr(request.state, "session_id", None)
    if not sid:
        raise HTTPException(status_code=500, detail="Session middleware not configured")
    return sid


# -----------------------------
# Routes (основные)
# -----------------------------
@router.post("/parcels/register", status_code=status.HTTP_202_ACCEPTED)
async def register_parcel(request: Request, data: ParcelRegisterIn):
    """
    Асинхронная регистрация через RabbitMQ:
    - генерируем `session_public_id` (UUID4 как строка без дефисов)
    - отправляем в очередь
    - отдаём public_id пользователю (в рамках его сессии он уникален)
    """
    session_id = get_session_id(request)
    session_public_id = uuid.uuid4().hex

    payload: dict[str, Any] = {
        "session_id": session_id,
        "session_public_id": session_public_id,
        "name": data.name,
        "weight_kg": str(data.weight_kg),
        "type_id": data.type_id,
        "content_usd": str(data.content_usd),
    }

    s = get_settings()
    await send_register_message(s.rabbitmq_url, payload)

    return ok({"public_id": session_public_id})


@router.post("/parcels/register-sync", status_code=status.HTTP_201_CREATED)
async def register_parcel_sync(
    request: Request,
    data: ParcelRegisterIn,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Синхронный путь (для отладки): создаёт Parcel напрямую.
    Сразу считает стоимость по текущему курсу.
    """
    from ..services.calc import calc_shipping
    from ..services.rates import get_redis_from_request

    redis = get_redis_from_request(request)
    usd_rub = await get_usd_rub(redis)

    session_public_id = uuid.uuid4().hex
    p = Parcel(
        session_id=get_session_id(request),
        session_public_id=session_public_id,
        name=data.name,
        weight_kg=Decimal(str(data.weight_kg)),
        type_id=data.type_id,
        content_usd=Decimal(str(data.content_usd)),
        cost_rub=calc_shipping(Decimal(str(data.weight_kg)), Decimal(str(data.content_usd)), usd_rub),
    )
    db.add(p)
    await db.flush()
    await db.commit()

    return ok(
        {
            "id": p.id,
            "public_id": p.session_public_id,
            "name": p.name,
            "weight_kg": str(p.weight_kg),
            "type_id": p.type_id,
            "content_usd": str(p.content_usd),
            "cost_rub": str(p.cost_rub) if p.cost_rub is not None else None,
        }
    )


@router.get("/parcels", response_model=Page)
async def list_parcels(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    type_id: int | None = Query(None, description="Фильтр по типу"),
    has_cost: bool | None = Query(None, description="Фильтр по факту наличия рассчитанной стоимости"),
    priced: bool | None = Query(None, description="Алиас has_cost"),
):
    session_id = get_session_id(request)
    if has_cost is None and priced is not None:
        has_cost = priced

    where = [Parcel.session_id == session_id]
    if type_id is not None:
        where.append(Parcel.type_id == type_id)
    if has_cost is not None:
        if has_cost:
            where.append(Parcel.cost_rub.is_not(None))
        else:
            where.append(Parcel.cost_rub.is_(None))

    total = await db.scalar(select(func.count()).select_from(select(Parcel.id).where(*where).subquery()))
    stmt = select(Parcel, ParcelType.name).join(ParcelType, ParcelType.id == Parcel.type_id).where(*where).order_by(Parcel.id.desc()).offset((page - 1) * per_page).limit(per_page)
    rows = (await db.execute(stmt)).all()

    items = [
        ParcelOut(
            id=prc.id,
            session_public_id=prc.session_public_id,
            name=prc.name,
            weight_kg=prc.weight_kg,
            type_id=prc.type_id,
            type_name=ptype_name,
            content_usd=prc.content_usd,
            cost_rub=prc.cost_rub,
            delivery_cost_rub=prc.cost_rub,
            shipping_company_id=prc.shipping_company_id,
        )
        for prc, ptype_name in rows
    ]
    return Page(items=items, page=page, per_page=per_page, total=int(total or 0))


# -----------------------------
# Compatibility alias endpoints (для внешних тестов)
# -----------------------------
class ParcelRegisterCompatIn(BaseModel):
    name: str
    weight: Decimal = Field(..., gt=Decimal("0"))
    type_id: int = Field(..., gt=0)
    declared_usd: Decimal = Field(..., ge=Decimal("0"))


class ParcelCompatOut(BaseModel):
    id: int
    name: str
    type_id: int
    type_name: str
    weight: Decimal = Field(serialization_alias="weight")
    content_usd: Decimal = Field(serialization_alias="declared_usd")
    cost_rub: Decimal | None

    model_config = {"populate_by_name": True}


@router.post("/parcels", status_code=status.HTTP_201_CREATED, response_model=ParcelCompatOut)
async def register_parcel_compat(
    request: Request,
    data: ParcelRegisterCompatIn,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Совместимый алиас под внешние тесты:
    - принимает name, weight, type_id, declared_usd
    - сохраняет напрямую (как /register-sync) и сразу считает стоимость
    - возвращает числовой id
    """
    from ..services.calc import calc_shipping
    from ..services.rates import get_redis_from_request

    # проверим наличие типа
    type_row = (await db.execute(select(ParcelType).where(ParcelType.id == data.type_id))).scalar_one_or_none()
    if not type_row:
        raise HTTPException(status_code=400, detail="Unknown type_id")

    redis = get_redis_from_request(request)
    usd_rub = await get_usd_rub(redis)

    p = Parcel(
        session_id=get_session_id(request),
        session_public_id=uuid.uuid4().hex,
        name=data.name,
        weight_kg=Decimal(str(data.weight)),
        type_id=data.type_id,
        content_usd=Decimal(str(data.declared_usd)),
        cost_rub=calc_shipping(Decimal(str(data.weight)), Decimal(str(data.declared_usd)), usd_rub),
    )
    db.add(p)
    await db.flush()
    await db.commit()

    return ParcelCompatOut(
        id=p.id,
        name=p.name,
        type_id=p.type_id,
        type_name=type_row.name,
        weight=p.weight_kg,
        content_usd=p.content_usd,
        cost_rub=p.cost_rub,
    )


@router.get("/parcels/{item_id:int}", response_model=ParcelCompatOut)
async def get_parcel_by_numeric_id(
    item_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Совместимый алиас: детальная по числовому id (в пределах текущей сессии).
    """
    session_id = get_session_id(request)
    row = (await db.execute(select(Parcel, ParcelType.name).join(ParcelType, ParcelType.id == Parcel.type_id).where(and_(Parcel.session_id == session_id, Parcel.id == item_id)).limit(1))).first()
    if not row:
        raise HTTPException(status_code=404, detail="Parcel not found")

    prc, ptype_name = row
    return ParcelCompatOut(
        id=prc.id,
        name=prc.name,
        type_id=prc.type_id,
        type_name=ptype_name,
        weight=prc.weight_kg,
        content_usd=prc.content_usd,
        cost_rub=prc.cost_rub,
    )


# -----------------------------
# Routes (основные)
# -----------------------------
@router.get("/parcels/{public_id}", response_model=ParcelOut)
async def get_parcel(
    public_id: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    session_id = get_session_id(request)
    stmt = select(Parcel, ParcelType.name).join(ParcelType, ParcelType.id == Parcel.type_id).where(and_(Parcel.session_id == session_id, Parcel.session_public_id == public_id)).limit(1)
    row = (await db.execute(stmt)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Parcel not found")

    prc, ptype_name = row
    return ParcelOut(
        id=prc.id,
        session_public_id=prc.session_public_id,
        name=prc.name,
        weight_kg=prc.weight_kg,
        type_id=prc.type_id,
        type_name=ptype_name,
        content_usd=prc.content_usd,
        cost_rub=prc.cost_rub,
        delivery_cost_rub=prc.cost_rub,
        shipping_company_id=prc.shipping_company_id,
    )


@router.post("/parcels/{public_id}/bind", status_code=status.HTTP_200_OK)
async def bind_parcel_to_company(
    public_id: str,
    company_id: Annotated[int, Query(gt=0)],
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Привязка перевозчика: «первый победил».
    Атомарно апдейтим только если поле ещё NULL.
    """
    session_id = get_session_id(request)

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
    res = await db.execute(stmt)
    if res.rowcount == 0:
        raise HTTPException(status_code=409, detail="Already bound or not found")
    await db.commit()
    return ok(True)
