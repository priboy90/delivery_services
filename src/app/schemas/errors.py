# src/app/schemas/errors.py
from __future__ import annotations

from typing import Any, TypedDict


class ErrorPayload(TypedDict, total=False):
    code: str
    message: str
    details: dict[str, Any]


class ApiEnvelope(TypedDict, total=False):
    ok: bool
    result: Any | None
    error: ErrorPayload | None
