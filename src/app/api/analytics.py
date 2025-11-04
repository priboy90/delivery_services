from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ..services.mongo import get_mongo_from_request
from .responses import ok

router = APIRouter(prefix="/analytics", tags=["analytics"])


class DailyStats(BaseModel):
    date_utc: str
    total_calcs: int
    avg_cost_rub: str | None
    sum_cost_rub: str | None


@router.get("/daily")
async def analytics_daily(
    date_utc: str = Query(default=None, description="YYYY-MM-DD (UTC), если не задано — сегодня"),
    limit: int = Query(default=7, ge=1, le=90),
    mongo: Annotated[object, Depends(get_mongo_from_request)] = None,
):
    if mongo is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Analytics storage is not configured")

    if date_utc:
        try:
            day = datetime.strptime(date_utc, "%Y-%m-%d").replace(tzinfo=UTC)
        except ValueError as err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format, expected YYYY-MM-DD") from err
        start = day
        end = day + timedelta(days=1)
        pipeline = [
            {"$match": {"ts": {"$gte": start, "$lt": end}}},
            {
                "$group": {
                    "_id": {"date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$ts"}}},
                    "total_calcs": {"$sum": 1},
                    "avg_cost_rub": {"$avg": {"$toDecimal": "$cost_rub"}},
                    "sum_cost_rub": {"$sum": {"$toDecimal": "$cost_rub"}},
                }
            },
            {"$sort": {"_id.date": -1}},
        ]
    else:
        pipeline = [
            {
                "$group": {
                    "_id": {"date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$ts"}}},
                    "total_calcs": {"$sum": 1},
                    "avg_cost_rub": {"$avg": {"$toDecimal": "$cost_rub"}},
                    "sum_cost_rub": {"$sum": {"$toDecimal": "$cost_rub"}},
                }
            },
            {"$sort": {"_id.date": -1}},
            {"$limit": limit},
        ]

    rows = await mongo.db["calc_logs"].aggregate(pipeline).to_list(length=limit if not date_utc else 1)
    items: list[DailyStats] = []
    for r in rows:
        items.append(
            DailyStats(
                date_utc=r["_id"]["date"],
                total_calcs=r["total_calcs"],
                avg_cost_rub=(str(r.get("avg_cost_rub")) if r.get("avg_cost_rub") is not None else None),
                sum_cost_rub=(str(r.get("sum_cost_rub")) if r.get("sum_cost_rub") is not None else None),
            )
        )
    return ok({"items": [i.model_dump() for i in items]})
