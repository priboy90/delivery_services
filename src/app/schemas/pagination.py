# FILE: src/app/schemas/pagination.py
from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import Field
from pydantic.generics import GenericModel

T = TypeVar("T")


class Page(GenericModel, Generic[T]):
    items: list[T] = Field(default_factory=list)
    page: int = 1
    per_page: int = 20
    total: int = 0
