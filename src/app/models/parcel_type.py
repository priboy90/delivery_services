from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .parcel import Parcel


class ParcelType(Base):
    __tablename__ = "parcel_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    parcels: Mapped[list[Parcel]] = relationship(
        "Parcel",
        back_populates="parcel_type",
        cascade="all, delete-orphan",
        passive_deletes=False,
    )
