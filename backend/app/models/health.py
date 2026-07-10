"""Home Health Record, warranty and warranty claim models."""
from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import WarrantyClaimStatus


class HealthRecord(Base):
    """Auto-generated when a job is closed. Immutable service history."""

    __tablename__ = "health_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[Optional[int]] = mapped_column(ForeignKey("properties.id"), index=True)
    asset_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assets.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_requests.id"), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    service_date: Mapped[Optional[date]] = mapped_column(Date)
    issue: Mapped[Optional[str]] = mapped_column(Text)
    diagnosis: Mapped[Optional[str]] = mapped_column(Text)
    work_performed: Mapped[Optional[str]] = mapped_column(Text)
    technician_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    technician_company: Mapped[Optional[str]] = mapped_column(String(255))
    parts_used: Mapped[Optional[list]] = mapped_column(JSON)
    labor_cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    parts_cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    total_cost: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    before_photos: Mapped[Optional[list]] = mapped_column(JSON)
    after_photos: Mapped[Optional[list]] = mapped_column(JSON)
    warranty_start: Mapped[Optional[date]] = mapped_column(Date)
    warranty_end: Mapped[Optional[date]] = mapped_column(Date)
    warranty_terms: Mapped[Optional[str]] = mapped_column(Text)
    next_inspection_date: Mapped[Optional[date]] = mapped_column(Date)
    next_maintenance_date: Mapped[Optional[date]] = mapped_column(Date)
    documents: Mapped[Optional[list]] = mapped_column(JSON)
    customer_notes: Mapped[Optional[str]] = mapped_column(Text)


class Warranty(Base):
    __tablename__ = "warranties"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_requests.id"), index=True)
    health_record_id: Mapped[Optional[int]] = mapped_column(ForeignKey("health_records.id"))
    has_warranty: Mapped[bool] = mapped_column(default=True)
    warranty_days: Mapped[Optional[int]] = mapped_column(Integer)
    covers_labor: Mapped[bool] = mapped_column(default=True)
    covers_parts: Mapped[bool] = mapped_column(default=True)
    exclusions: Mapped[Optional[str]] = mapped_column(Text)
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date, index=True)


class WarrantyClaim(Base):
    __tablename__ = "warranty_claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    original_job_id: Mapped[int] = mapped_column(ForeignKey("job_requests.id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    evidence: Mapped[Optional[list]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(
        String(32), default=WarrantyClaimStatus.submitted.value, index=True
    )
    assigned_technician_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    resolution: Mapped[Optional[str]] = mapped_column(Text)
    cost_responsibility: Mapped[Optional[str]] = mapped_column(String(64))
