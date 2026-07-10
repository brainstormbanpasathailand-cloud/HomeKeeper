"""Property and asset models."""
from datetime import date
from typing import Optional

from sqlalchemy import Date, Float, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import AssetStatus


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    property_type: Mapped[str] = mapped_column(String(32), index=True)
    address: Mapped[Optional[str]] = mapped_column(Text)
    province: Mapped[Optional[str]] = mapped_column(String(128))
    district: Mapped[Optional[str]] = mapped_column(String(128))
    subdistrict: Mapped[Optional[str]] = mapped_column(String(128))
    postal_code: Mapped[Optional[str]] = mapped_column(String(16))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    access_instruction: Mapped[Optional[str]] = mapped_column(Text)
    floor: Mapped[Optional[str]] = mapped_column(String(32))
    unit_number: Mapped[Optional[str]] = mapped_column(String(64))
    year_built: Mapped[Optional[int]] = mapped_column(Integer)
    usable_area: Mapped[Optional[float]] = mapped_column(Float)
    photos: Mapped[Optional[list]] = mapped_column(JSON)

    assets: Mapped[list["Asset"]] = relationship(
        back_populates="property", cascade="all, delete-orphan"
    )


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id", ondelete="CASCADE"), index=True
    )
    asset_category: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(255))
    brand: Mapped[Optional[str]] = mapped_column(String(128))
    model: Mapped[Optional[str]] = mapped_column(String(128))
    serial_number: Mapped[Optional[str]] = mapped_column(String(128))
    purchase_date: Mapped[Optional[date]] = mapped_column(Date)
    installation_date: Mapped[Optional[date]] = mapped_column(Date)
    purchase_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    warranty_start: Mapped[Optional[date]] = mapped_column(Date)
    warranty_end: Mapped[Optional[date]] = mapped_column(Date)
    receipt_url: Mapped[Optional[str]] = mapped_column(String(1024))
    manual_url: Mapped[Optional[str]] = mapped_column(String(1024))
    photos: Mapped[Optional[list]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default=AssetStatus.active.value)
    maintenance_interval_days: Mapped[Optional[int]] = mapped_column(Integer)
    next_maintenance_date: Mapped[Optional[date]] = mapped_column(Date)

    property: Mapped["Property"] = relationship(back_populates="assets")
