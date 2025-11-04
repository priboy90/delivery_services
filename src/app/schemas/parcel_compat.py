from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class ParcelRegisterCompatIn(BaseModel):
    """
    Совместимый вход: name, weight, type_id, declared_usd
    """

    name: str
    weight: Decimal = Field(gt=0)
    type_id: int = Field(gt=0)
    declared_usd: Decimal = Field(ge=0)


class ParcelCompatOut(BaseModel):
    """
    Совместимый выход: числовой id и поля с алиасами как в старом контракте.
    """

    id: int
    name: str
    type_id: int
    type_name: str
    weight: Decimal = Field(serialization_alias="weight")
    content_usd: Decimal = Field(serialization_alias="declared_usd")
    cost_rub: Decimal | None

    model_config = {"populate_by_name": True}
