"""Property and asset schemas."""
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class PropertyBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    property_type: str
    address: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    subdistrict: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    access_instruction: Optional[str] = None
    floor: Optional[str] = None
    unit_number: Optional[str] = None
    year_built: Optional[int] = None
    usable_area: Optional[float] = None
    photos: Optional[List[str]] = None


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    property_type: Optional[str] = None
    address: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    subdistrict: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    access_instruction: Optional[str] = None
    floor: Optional[str] = None
    unit_number: Optional[str] = None
    year_built: Optional[int] = None
    usable_area: Optional[float] = None
    photos: Optional[List[str]] = None


class PropertyOut(PropertyBase):
    id: int
    owner_id: int

    model_config = {"from_attributes": True}


class AssetBase(BaseModel):
    asset_category: Optional[str] = None
    name: str = Field(min_length=1, max_length=255)
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[date] = None
    installation_date: Optional[date] = None
    purchase_price: Optional[float] = None
    warranty_start: Optional[date] = None
    warranty_end: Optional[date] = None
    receipt_url: Optional[str] = None
    manual_url: Optional[str] = None
    photos: Optional[List[str]] = None
    status: Optional[str] = "active"
    maintenance_interval_days: Optional[int] = None
    next_maintenance_date: Optional[date] = None


class AssetCreate(AssetBase):
    pass


class AssetUpdate(AssetBase):
    name: Optional[str] = None


class AssetOut(AssetBase):
    id: int
    property_id: int

    model_config = {"from_attributes": True}
