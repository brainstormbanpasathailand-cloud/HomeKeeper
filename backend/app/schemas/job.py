"""Job request, assignment and quotation schemas."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    service_category_id: int
    title: str = Field(min_length=1, max_length=255)
    property_id: Optional[int] = None
    asset_id: Optional[int] = None
    urgency: str = "scheduled"
    problem_description: Optional[str] = None
    # The customer must attach at least one photo of the issue (up to 10).
    photos: List[str] = Field(min_length=1, max_length=10)
    videos: Optional[List[str]] = None
    preferred_date: Optional[datetime] = None
    preferred_time_start: Optional[str] = None
    preferred_time_end: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_phone: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    language_preference: Optional[str] = None
    requires_certified_technician: bool = False
    requires_english_speaking: bool = False


class JobOut(BaseModel):
    id: int
    job_number: str
    customer_id: int
    service_category_id: int
    property_id: Optional[int]
    asset_id: Optional[int]
    urgency: str
    title: str
    problem_description: Optional[str]
    status: str
    assigned_technician_id: Optional[int]
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    photos: Optional[List[str]]
    preferred_date: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignRequest(BaseModel):
    technician_id: int
    note: Optional[str] = None


class StatusUpdateRequest(BaseModel):
    status: str
    note: Optional[str] = None


class AssignmentResponse(BaseModel):
    accept: bool
    note: Optional[str] = None


class JobMediaCreate(BaseModel):
    kind: str = "document"
    url: str
    caption: Optional[str] = None


class QuotationItemIn(BaseModel):
    description: str
    quantity: float = 1
    unit_price: float = 0


class PartIn(BaseModel):
    part_name: str
    brand: Optional[str] = None
    model: Optional[str] = None
    quantity: float = 1
    unit_price: float = 0
    supplier: Optional[str] = None
    warranty_period_days: Optional[int] = None
    authenticity: str = "compatible"
    serial_number: Optional[str] = None


class QuotationCreate(BaseModel):
    labor_cost: float = 0
    travel_cost: float = 0
    inspection_fee: float = 0
    emergency_surcharge: float = 0
    other_charges: float = 0
    discount: float = 0
    platform_fee: float = 0
    vat: float = 0
    notes: Optional[str] = None
    valid_until: Optional[datetime] = None
    items: List[QuotationItemIn] = []
    parts: List[PartIn] = []


class QuotationOut(BaseModel):
    id: int
    job_id: int
    technician_id: int
    version: int
    labor_cost: float
    travel_cost: float
    inspection_fee: float
    emergency_surcharge: float
    other_charges: float
    discount: float
    platform_fee: float
    vat: float
    total: float
    notes: Optional[str]
    status: str
    valid_until: Optional[datetime]

    model_config = {"from_attributes": True}


class QuotationDecision(BaseModel):
    decision: str = Field(pattern="^(approve|reject|revision)$")
    note: Optional[str] = None
