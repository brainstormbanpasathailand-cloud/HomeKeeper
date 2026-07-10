"""Service category schemas."""
from typing import Optional

from pydantic import BaseModel, Field


class ServiceCategoryBase(BaseModel):
    name_th: str
    name_en: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    requires_certification: bool = False


class ServiceCategoryCreate(ServiceCategoryBase):
    slug: str = Field(min_length=1, max_length=128)


class ServiceCategoryUpdate(BaseModel):
    name_th: Optional[str] = None
    name_en: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    requires_certification: Optional[bool] = None


class ServiceCategoryOut(ServiceCategoryBase):
    id: int
    slug: str

    model_config = {"from_attributes": True}


class ReorderRequest(BaseModel):
    ordered_ids: list[int]
