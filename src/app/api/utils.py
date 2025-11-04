from __future__ import annotations

from fastapi import HTTPException, Request, status


def ensure_session_id(request: Request) -> str:
    """
     Возвращает session_id из header/cookie/query/state, либо 500 если его нет.
    Полностью синхронный (НЕ вызывает async-функции).
    """
    sid = request.headers.get("X-Session-Id") or request.cookies.get("session_id") or request.query_params.get("session_id") or getattr(request.state, "session_id", None)
    if not sid:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Session is not initialized")

    request.state.session_id = sid

    return sid
