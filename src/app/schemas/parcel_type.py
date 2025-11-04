from __future__ import annotations

from pydantic import BaseModel


class ParcelTypeOut(BaseModel):
    id: int
    name: str
