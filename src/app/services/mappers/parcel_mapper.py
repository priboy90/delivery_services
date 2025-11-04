from __future__ import annotations

from ...models.parcel import Parcel


def to_public_dict(parc: Parcel, type_name: str) -> dict:
    return {
        "public_id": parc.session_public_id,
        "name": parc.name,
        "type_id": parc.type_id,
        "type_name": type_name,
        "weight_kg": parc.weight_kg,
        "content_usd": parc.content_usd,
        "cost_rub": parc.cost_rub,
        "shipping_company_id": parc.shipping_company_id,
    }
