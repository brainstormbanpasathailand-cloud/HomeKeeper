"""Offset pagination helper shared by list endpoints."""
import math
from typing import Any

from fastapi import Query
from sqlalchemy.orm import Query as OrmQuery

from app.schemas.common import Page


class PageParams:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        size: int = Query(20, ge=1, le=100),
    ):
        self.page = page
        self.size = size


def paginate(query: OrmQuery, params: PageParams) -> Page[Any]:
    total = query.count()
    items = query.offset((params.page - 1) * params.size).limit(params.size).all()
    return Page(
        items=items,
        total=total,
        page=params.page,
        size=params.size,
        pages=math.ceil(total / params.size) if params.size else 0,
    )
