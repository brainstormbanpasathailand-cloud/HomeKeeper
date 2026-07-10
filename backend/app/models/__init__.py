"""Import all models so that Base.metadata is fully populated."""
from app.models.catalog import ServiceCategory, ServiceSubcategory
from app.models.health import HealthRecord, Warranty, WarrantyClaim
from app.models.job import JobAssignment, JobMedia, JobRequest, JobStatusHistory
from app.models.misc import (
    AuditLog,
    Coupon,
    CouponRedemption,
    Dispute,
    Notification,
    Payment,
    Payout,
    Review,
)
from app.models.property import Asset, Property
from app.models.quotation import Part, Quotation, QuotationItem
from app.models.technician import (
    TechnicianAvailability,
    TechnicianCertificate,
    TechnicianProfile,
    TechnicianServiceCategory,
)
from app.models.user import (
    AuthIdentity,
    TermsAcceptance,
    User,
    UserAddress,
    UserSession,
)

__all__ = [
    "User",
    "AuthIdentity",
    "UserSession",
    "UserAddress",
    "TermsAcceptance",
    "TechnicianProfile",
    "TechnicianCertificate",
    "TechnicianServiceCategory",
    "TechnicianAvailability",
    "ServiceCategory",
    "ServiceSubcategory",
    "Property",
    "Asset",
    "JobRequest",
    "JobAssignment",
    "JobStatusHistory",
    "JobMedia",
    "Quotation",
    "QuotationItem",
    "Part",
    "HealthRecord",
    "Warranty",
    "WarrantyClaim",
    "Review",
    "Coupon",
    "CouponRedemption",
    "Notification",
    "Payment",
    "Payout",
    "Dispute",
    "AuditLog",
]
