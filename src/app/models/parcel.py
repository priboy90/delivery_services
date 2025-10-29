# FILE: src/app/models/parcel.py

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .parcel_type import ParcelType


class Parcel(Base):
    __tablename__ = "parcels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    session_public_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)

    type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("parcel_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    parcel_type: Mapped[ParcelType] = relationship(
        "ParcelType",
        back_populates="parcels",
        lazy="joined",
    )

    content_usd: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cost_rub: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    shipping_company_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    __table_args__ = (UniqueConstraint("session_id", "session_public_id", name="uq_parcels_session_public"),)
