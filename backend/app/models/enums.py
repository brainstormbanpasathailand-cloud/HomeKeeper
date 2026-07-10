"""Enumerations used across the domain models.

Stored as plain strings in the database for portability (SQLite in tests,
PostgreSQL in production) and to allow adding values without a migration on
enum types. Validation happens at the Pydantic / service layer.
"""
import enum


class UserRole(str, enum.Enum):
    customer = "customer"
    technician = "technician"
    admin = "admin"
    super_admin = "super_admin"
    support = "support"
    dispatcher = "dispatcher"


class AuthProvider(str, enum.Enum):
    password = "password"
    line = "line"
    google = "google"
    facebook = "facebook"
    phone = "phone"


class VerificationStatus(str, enum.Enum):
    pending = "pending"
    submitted = "submitted"
    under_review = "under_review"
    approved = "approved"
    rejected = "rejected"


class OnlineStatus(str, enum.Enum):
    offline = "offline"
    online = "online"


class AvailabilityStatus(str, enum.Enum):
    unavailable = "unavailable"
    available = "available"
    busy = "busy"


class PropertyType(str, enum.Enum):
    house = "house"
    condo = "condo"
    building = "building"
    shop = "shop"
    office = "office"
    car = "car"
    motorcycle = "motorcycle"


class AssetStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    needs_service = "needs_service"
    retired = "retired"


class Urgency(str, enum.Enum):
    emergency = "emergency"
    today = "today"
    scheduled = "scheduled"
    quote_first = "quote_first"
    project = "project"


class JobStatus(str, enum.Enum):
    draft = "draft"
    requested = "requested"
    reviewing = "reviewing"
    searching = "searching"
    assigned = "assigned"
    accepted = "accepted"
    rejected = "rejected"
    traveling = "traveling"
    arrived = "arrived"
    inspecting = "inspecting"
    quoted = "quoted"
    quotation_revision_requested = "quotation_revision_requested"
    approved = "approved"
    in_progress = "in_progress"
    paused = "paused"
    completed = "completed"
    customer_confirmed = "customer_confirmed"
    cancelled = "cancelled"
    disputed = "disputed"
    warranty_claim = "warranty_claim"
    closed = "closed"


class AssignmentStatus(str, enum.Enum):
    offered = "offered"
    accepted = "accepted"
    rejected = "rejected"
    reassigned = "reassigned"
    completed = "completed"


class QuotationStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    approved = "approved"
    rejected = "rejected"
    revision_requested = "revision_requested"
    expired = "expired"


class PartAuthenticity(str, enum.Enum):
    genuine = "genuine"
    oem = "oem"
    compatible = "compatible"
    used = "used"


class MediaKind(str, enum.Enum):
    before = "before"
    during = "during"
    after = "after"
    document = "document"
    request = "request"


class WarrantyClaimStatus(str, enum.Enum):
    submitted = "submitted"
    reviewing = "reviewing"
    approved = "approved"
    rejected = "rejected"
    resolved = "resolved"


class NotificationType(str, enum.Enum):
    account_created = "account_created"
    technician_approved = "technician_approved"
    new_job = "new_job"
    job_accepted = "job_accepted"
    technician_traveling = "technician_traveling"
    technician_arrived = "technician_arrived"
    quotation_created = "quotation_created"
    quotation_approved = "quotation_approved"
    job_completed = "job_completed"
    review_requested = "review_requested"
    warranty_expiring = "warranty_expiring"
    maintenance_due = "maintenance_due"
    warranty_claim_update = "warranty_claim_update"
    promotion = "promotion"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    refunded = "refunded"
    failed = "failed"
