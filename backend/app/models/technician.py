"""Technician profile, certificates, category skills and availability."""
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import AvailabilityStatus, OnlineStatus, VerificationStatus


class TechnicianProfile(Base):
    __tablename__ = "technician_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    legal_name: Mapped[Optional[str]] = mapped_column(String(255))
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    national_id_or_passport: Mapped[Optional[str]] = mapped_column(String(64))
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_photo: Mapped[Optional[str]] = mapped_column(String(1024))
    identity_document_front: Mapped[Optional[str]] = mapped_column(String(1024))
    identity_document_back: Mapped[Optional[str]] = mapped_column(String(1024))
    selfie_with_document: Mapped[Optional[str]] = mapped_column(String(1024))
    address: Mapped[Optional[str]] = mapped_column(Text)
    province: Mapped[Optional[str]] = mapped_column(String(128))
    district: Mapped[Optional[str]] = mapped_column(String(128))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    location_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    service_radius_km: Mapped[float] = mapped_column(Float, default=10.0)
    years_of_experience: Mapped[Optional[int]] = mapped_column(Integer)
    languages: Mapped[Optional[list]] = mapped_column(JSON)
    bio: Mapped[Optional[str]] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(
        String(32), default=VerificationStatus.pending.value, index=True
    )
    average_rating: Mapped[float] = mapped_column(Float, default=0.0)
    completed_jobs: Mapped[int] = mapped_column(Integer, default=0)
    acceptance_rate: Mapped[float] = mapped_column(Float, default=0.0)
    cancellation_rate: Mapped[float] = mapped_column(Float, default=0.0)
    online_status: Mapped[str] = mapped_column(String(16), default=OnlineStatus.offline.value)
    availability_status: Mapped[str] = mapped_column(
        String(16), default=AvailabilityStatus.unavailable.value
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))

    certificates: Mapped[list["TechnicianCertificate"]] = relationship(
        back_populates="technician", cascade="all, delete-orphan"
    )
    service_categories: Mapped[list["TechnicianServiceCategory"]] = relationship(
        back_populates="technician", cascade="all, delete-orphan"
    )
    availability: Mapped[list["TechnicianAvailability"]] = relationship(
        back_populates="technician", cascade="all, delete-orphan"
    )


class TechnicianCertificate(Base):
    __tablename__ = "technician_certificates"

    id: Mapped[int] = mapped_column(primary_key=True)
    technician_id: Mapped[int] = mapped_column(
        ForeignKey("technician_profiles.id", ondelete="CASCADE"), index=True
    )
    certificate_type: Mapped[str] = mapped_column(String(128))
    certificate_number: Mapped[Optional[str]] = mapped_column(String(128))
    issuer: Mapped[Optional[str]] = mapped_column(String(255))
    issue_date: Mapped[Optional[date]] = mapped_column(Date)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date)
    document_url: Mapped[Optional[str]] = mapped_column(String(1024))
    verification_status: Mapped[str] = mapped_column(
        String(32), default=VerificationStatus.pending.value
    )
    verified_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    technician: Mapped["TechnicianProfile"] = relationship(back_populates="certificates")


class TechnicianServiceCategory(Base):
    __tablename__ = "technician_service_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    technician_id: Mapped[int] = mapped_column(
        ForeignKey("technician_profiles.id", ondelete="CASCADE"), index=True
    )
    service_category_id: Mapped[int] = mapped_column(
        ForeignKey("service_categories.id", ondelete="CASCADE"), index=True
    )
    skill_level: Mapped[Optional[str]] = mapped_column(String(32))
    min_call_fee: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    accepts_emergency: Mapped[bool] = mapped_column(Boolean, default=False)
    accepts_scheduled: Mapped[bool] = mapped_column(Boolean, default=True)

    technician: Mapped["TechnicianProfile"] = relationship(back_populates="service_categories")


class TechnicianAvailability(Base):
    __tablename__ = "technician_availability"

    id: Mapped[int] = mapped_column(primary_key=True)
    technician_id: Mapped[int] = mapped_column(
        ForeignKey("technician_profiles.id", ondelete="CASCADE"), index=True
    )
    day_of_week: Mapped[int] = mapped_column(Integer)  # 0=Monday
    start_time: Mapped[Optional[str]] = mapped_column(String(8))  # "08:00"
    end_time: Mapped[Optional[str]] = mapped_column(String(8))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    technician: Mapped["TechnicianProfile"] = relationship(back_populates="availability")
