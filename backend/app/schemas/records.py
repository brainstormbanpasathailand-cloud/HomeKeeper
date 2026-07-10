"""Health record, warranty, review, notification and technician schemas."""
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class HealthRecordOut(BaseModel):
    id: int
    property_id: Optional[int]
    asset_id: Optional[int]
    job_id: int
    service_date: Optional[date]
    issue: Optional[str]
    diagnosis: Optional[str]
    work_performed: Optional[str]
    technician_id: Optional[int]
    parts_used: Optional[list]
    labor_cost: Optional[float]
    parts_cost: Optional[float]
    total_cost: Optional[float]
    before_photos: Optional[list]
    after_photos: Optional[list]
    warranty_start: Optional[date]
    warranty_end: Optional[date]
    next_inspection_date: Optional[date]
    next_maintenance_date: Optional[date]

    model_config = {"from_attributes": True}


class WarrantyClaimCreate(BaseModel):
    original_job_id: int
    reason: str
    evidence: Optional[List[str]] = None


class WarrantyClaimOut(BaseModel):
    id: int
    original_job_id: int
    customer_id: int
    reason: Optional[str]
    status: str
    resolution: Optional[str]

    model_config = {"from_attributes": True}


class ReviewCreate(BaseModel):
    rating_quality: int = Field(ge=1, le=5)
    rating_punctuality: Optional[int] = Field(default=None, ge=1, le=5)
    rating_politeness: Optional[int] = Field(default=None, ge=1, le=5)
    rating_cleanliness: Optional[int] = Field(default=None, ge=1, le=5)
    rating_value: Optional[int] = Field(default=None, ge=1, le=5)
    rating_communication: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = None
    photos: Optional[List[str]] = None


class ReviewOut(BaseModel):
    id: int
    job_id: int
    customer_id: int
    technician_id: int
    overall_rating: Optional[float]
    comment: Optional[str]
    is_hidden: bool

    model_config = {"from_attributes": True}


class NotificationOut(BaseModel):
    id: int
    type: str
    title: str
    body: Optional[str]
    data: Optional[dict]
    is_read: bool

    model_config = {"from_attributes": True}


class TechnicianApplyRequest(BaseModel):
    legal_name: str
    display_name: Optional[str] = None
    national_id_or_passport: Optional[str] = None
    phone: Optional[str] = None
    province: Optional[str] = None
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    service_radius_km: Optional[float] = 10.0
    years_of_experience: Optional[int] = None
    languages: Optional[List[str]] = None
    bio: Optional[str] = None
    category_ids: Optional[List[int]] = None


class TechnicianProfileOut(BaseModel):
    id: int
    user_id: int
    legal_name: Optional[str]
    display_name: Optional[str]
    verification_status: str
    average_rating: float
    completed_jobs: int
    online_status: str
    availability_status: str

    model_config = {"from_attributes": True}


class TechnicianReviewDecision(BaseModel):
    approve: bool
    reason: Optional[str] = None
