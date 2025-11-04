from __future__ import annotations

from fastapi import HTTPException, Request, status


def current_session_id(request: Request) -> str:
    sid = getattr(request.state, "session_id", None)
    if not sid:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Session is not initialized")
    return sid
