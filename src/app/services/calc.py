from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def calc_shipping(weight_kg: Decimal, content_usd: Decimal, usd_rub: Decimal) -> Decimal:
    """
    Формула из ТЗ:
    Стоимость = (вес_кг * 0.5 + стоимость_в_долларах * 0.01) * курс_USD_RUB
    Округлим до копеек банковским правилом.
    """
    base = (weight_kg * Decimal("0.5")) + (content_usd * Decimal("0.01"))
    cost = base * usd_rub
    return cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
