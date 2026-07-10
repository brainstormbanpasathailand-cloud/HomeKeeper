"""Quotation, quotation items and parts models."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import PartAuthenticity, QuotationStatus


class Quotation(Base):
    __tablename__ = "quotations"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_requests.id", ondelete="CASCADE"), index=True)
    technician_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    labor_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    travel_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    inspection_fee: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    emergency_surcharge: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    other_charges: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    discount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    platform_fee: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    vat: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    total: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default=QuotationStatus.draft.value, index=True)
    customer_response_note: Mapped[Optional[str]] = mapped_column(Text)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    items: Mapped[list["QuotationItem"]] = relationship(
        back_populates="quotation", cascade="all, delete-orphan"
    )
    parts: Mapped[list["Part"]] = relationship(
        back_populates="quotation", cascade="all, delete-orphan"
    )


class QuotationItem(Base):
    __tablename__ = "quotation_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    quotation_id: Mapped[int] = mapped_column(
        ForeignKey("quotations.id", ondelete="CASCADE"), index=True
    )
    description: Mapped[str] = mapped_column(String(512))
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)

    quotation: Mapped["Quotation"] = relationship(back_populates="items")


class Part(Base):
    __tablename__ = "parts"

    id: Mapped[int] = mapped_column(primary_key=True)
    quotation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("quotations.id", ondelete="CASCADE"))
    job_id: Mapped[Optional[int]] = mapped_column(ForeignKey("job_requests.id", ondelete="CASCADE"))
    part_name: Mapped[str] = mapped_column(String(255))
    brand: Mapped[Optional[str]] = mapped_column(String(128))
    model: Mapped[Optional[str]] = mapped_column(String(128))
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    supplier: Mapped[Optional[str]] = mapped_column(String(255))
    warranty_period_days: Mapped[Optional[int]] = mapped_column(Integer)
    receipt_url: Mapped[Optional[str]] = mapped_column(String(1024))
    serial_number: Mapped[Optional[str]] = mapped_column(String(128))
    authenticity: Mapped[str] = mapped_column(String(32), default=PartAuthenticity.compatible.value)

    quotation: Mapped[Optional["Quotation"]] = relationship(back_populates="parts")
