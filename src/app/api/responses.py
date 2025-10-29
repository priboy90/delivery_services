from __future__ import annotations

from typing import Any, TypedDict


class ErrorPayload(TypedDict, total=False):
    code: str
    message: str
    details: dict[str, Any]


def ok(result: Any) -> dict[str, Any]:
    return {"ok": True, "result": result, "error": None}


def err(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: ErrorPayload = {"code": code, "message": message}
    if details:
        payload["details"] = details
    return {"ok": False, "result": None, "error": payload}
