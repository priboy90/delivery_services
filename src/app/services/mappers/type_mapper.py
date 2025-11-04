from __future__ import annotations

from ...models.parcel_type import ParcelType


def to_public_dict(t: ParcelType) -> dict:
    return {"id": t.id, "name": t.name}
