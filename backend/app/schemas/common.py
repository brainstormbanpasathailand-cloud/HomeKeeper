"""Shared schema helpers: pagination envelope and error format."""
from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int


class Message(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
