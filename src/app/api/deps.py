# src/app/api/deps.py
from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.postgres import get_session_factory


def current_session_id(request: Request) -> str:
    sid = getattr(request.state, "session_id", None)
    if not sid:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Session is not initialized")
    return sid


async def get_db() -> AsyncIterator[AsyncSession]:
    Session = get_session_factory()
    async with Session() as session:
        yield session
