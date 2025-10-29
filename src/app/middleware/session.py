# src/app/middleware/session.py
from __future__ import annotations

import uuid

from fastapi import Cookie, Header, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

__all__ = ["get_session_id", "EnsureSessionIDMiddleware", "SessionMiddleware"]


async def get_session_id(
    request: Request,
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
    session_id_cookie: str | None = Cookie(default=None, alias="session_id"),
) -> str | None:
    """
    Универсальный способ получить session_id:
    1) заголовок X-Session-Id
    2) cookie session_id
    3) query-параметр ?session_id=...
    4) request.state.session_id, если middleware его установил
    """
    if x_session_id:
        sid = x_session_id.strip()
        if sid:
            request.state.session_id = sid
            return sid

    if session_id_cookie:
        sid = session_id_cookie.strip()
        if sid:
            request.state.session_id = sid
            return sid

    sid = (request.query_params.get("session_id") or "").strip()
    if sid:
        request.state.session_id = sid
        return sid

    return getattr(request.state, "session_id", None)


class EnsureSessionIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware, который гарантирует наличие session_id.
    Если клиент не прислал его заголовком/кукой/квери — генерируем и кладём в cookie.
    """

    def __init__(self, app: ASGIApp, cookie_max_age: int = 60 * 60 * 24 * 30) -> None:
        super().__init__(app)
        self.cookie_max_age = cookie_max_age

    async def dispatch(self, request: Request, call_next):
        sid = request.headers.get("X-Session-Id") or request.cookies.get("session_id") or request.query_params.get("session_id")
        generated = False
        if not sid:
            sid = uuid.uuid4().hex
            generated = True

        request.state.session_id = sid
        response = await call_next(request)

        if generated and "session_id" not in response.headers.get("set-cookie", ""):
            response.set_cookie(
                key="session_id",
                value=sid,
                httponly=True,
                samesite="lax",
                max_age=self.cookie_max_age,
            )
        return response


# Алиас, чтобы существующий импорт `SessionMiddleware` продолжал работать
SessionMiddleware = EnsureSessionIDMiddleware
