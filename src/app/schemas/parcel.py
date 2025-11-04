from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ParcelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=500)
    weight_kg: Decimal = Field(gt=0)
    type_id: int = Field(gt=0)
    content_usd: Decimal = Field(ge=0)

    @field_validator("weight_kg", "content_usd", mode="before")
    @classmethod
    def _ensure_decimal_str(cls, v):
        return str(v)


class ParcelOut(BaseModel):
    public_id: str
    name: str
    type_id: int
    type_name: str
    weight_kg: Decimal
    content_usd: Decimal
    cost_rub: Decimal | None = None
    shipping_company_id: int | None = None

    model_config = ConfigDict(from_attributes=True)
