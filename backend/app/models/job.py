"""Job request, assignment, status history and media models."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import AssignmentStatus, JobStatus, MediaKind, Urgency


class JobRequest(Base):
    __tablename__ = "job_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    property_id: Mapped[Optional[int]] = mapped_column(ForeignKey("properties.id"))
    asset_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assets.id"))
    service_category_id: Mapped[int] = mapped_column(
        ForeignKey("service_categories.id"), index=True
    )
    urgency: Mapped[str] = mapped_column(String(32), default=Urgency.scheduled.value)
    title: Mapped[str] = mapped_column(String(255))
    problem_description: Mapped[Optional[str]] = mapped_column(Text)
    photos: Mapped[Optional[list]] = mapped_column(JSON)
    videos: Mapped[Optional[list]] = mapped_column(JSON)
    preferred_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    preferred_time_start: Mapped[Optional[str]] = mapped_column(String(8))
    preferred_time_end: Mapped[Optional[str]] = mapped_column(String(8))
    address: Mapped[Optional[str]] = mapped_column(Text)
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(32))
    budget_min: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    budget_max: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    language_preference: Mapped[Optional[str]] = mapped_column(String(8))
    requires_certified_technician: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_english_speaking: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default=JobStatus.requested.value, index=True)
    assigned_technician_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), index=True)

    assignments: Mapped[list["JobAssignment"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    status_history: Mapped[list["JobStatusHistory"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
    media: Mapped[list["JobMedia"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class JobAssignment(Base):
    __tablename__ = "job_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_requests.id", ondelete="CASCADE"), index=True)
    technician_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    assigned_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(32), default=AssignmentStatus.offered.value)
    note: Mapped[Optional[str]] = mapped_column(Text)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    job: Mapped["JobRequest"] = relationship(back_populates="assignments")


class JobStatusHistory(Base):
    __tablename__ = "job_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_requests.id", ondelete="CASCADE"), index=True)
    from_status: Mapped[Optional[str]] = mapped_column(String(32))
    to_status: Mapped[str] = mapped_column(String(32))
    changed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    note: Mapped[Optional[str]] = mapped_column(Text)

    job: Mapped["JobRequest"] = relationship(back_populates="status_history")


class JobMedia(Base):
    __tablename__ = "job_media"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_requests.id", ondelete="CASCADE"), index=True)
    uploaded_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    kind: Mapped[str] = mapped_column(String(32), default=MediaKind.document.value)
    url: Mapped[str] = mapped_column(String(1024))
    caption: Mapped[Optional[str]] = mapped_column(String(512))

    job: Mapped["JobRequest"] = relationship(back_populates="media")
