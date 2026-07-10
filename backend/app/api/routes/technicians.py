"""Technician onboarding and admin verification."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models.enums import NotificationType, UserRole, VerificationStatus
from app.models.technician import (
    TechnicianCertificate,
    TechnicianProfile,
    TechnicianServiceCategory,
)
from app.models.user import User
from app.schemas.common import Message
from app.schemas.records import (
    TechnicianApplyRequest,
    TechnicianDetailOut,
    TechnicianProfileOut,
    TechnicianReviewDecision,
)
from app.services.audit import log_action
from app.services.notifications import notify

router = APIRouter(prefix="/technicians", tags=["technicians"])


def _serialize_detail(db: Session, profile: TechnicianProfile) -> dict:
    tech_user = db.get(User, profile.user_id)
    return {
        **{c.name: getattr(profile, c.name) for c in profile.__table__.columns},
        "phone": tech_user.phone if tech_user else None,
        "email": tech_user.email if tech_user else None,
        "certificates": profile.certificates,
        "categories": profile.service_categories,
    }


@router.post("/apply", response_model=TechnicianProfileOut, status_code=status.HTTP_201_CREATED)
def apply_as_technician(
    payload: TechnicianApplyRequest, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    existing = db.query(TechnicianProfile).filter(TechnicianProfile.user_id == user.id).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Technician profile already exists")
    profile = TechnicianProfile(
        user_id=user.id,
        legal_name=payload.legal_name,
        display_name=payload.display_name or user.display_name,
        national_id_or_passport=payload.national_id_or_passport,
        date_of_birth=payload.date_of_birth,
        province=payload.province,
        district=payload.district,
        latitude=payload.latitude,
        longitude=payload.longitude,
        service_radius_km=payload.service_radius_km or 10.0,
        years_of_experience=payload.years_of_experience,
        languages=payload.languages,
        bio=payload.bio,
        profile_photo=payload.profile_photo,
        identity_document_front=payload.identity_document_front,
        identity_document_back=payload.identity_document_back,
        selfie_with_document=payload.selfie_with_document,
        phone_verified=user.phone_verified,
        email_verified=user.email_verified,
        verification_status=VerificationStatus.submitted.value,
    )
    db.add(profile)
    db.flush()

    # Categories: rich form preferred, simple id list as fallback.
    if payload.categories:
        for c in payload.categories:
            db.add(
                TechnicianServiceCategory(
                    technician_id=profile.id,
                    service_category_id=c.service_category_id,
                    skill_level=c.skill_level,
                    min_call_fee=c.min_call_fee,
                    accepts_emergency=c.accepts_emergency,
                    accepts_scheduled=c.accepts_scheduled,
                )
            )
    else:
        for cid in payload.category_ids or []:
            db.add(TechnicianServiceCategory(technician_id=profile.id, service_category_id=cid))

    for cert in payload.certificates:
        db.add(
            TechnicianCertificate(
                technician_id=profile.id,
                certificate_type=cert.certificate_type,
                certificate_number=cert.certificate_number,
                issuer=cert.issuer,
                issue_date=cert.issue_date,
                expiry_date=cert.expiry_date,
                document_url=cert.document_url,
                verification_status=VerificationStatus.pending.value,
            )
        )

    log_action(db, "technician.apply", actor_id=user.id, entity_type="technician_profile", entity_id=profile.id, request=request)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me", response_model=TechnicianProfileOut)
def my_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(TechnicianProfile).filter(TechnicianProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No technician profile")
    return profile


@router.get("/pending", response_model=list[TechnicianProfileOut])
def pending_technicians(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return (
        db.query(TechnicianProfile)
        .filter(TechnicianProfile.verification_status.in_([VerificationStatus.submitted.value, VerificationStatus.under_review.value]))
        .all()
    )


@router.get("/{profile_id}", response_model=TechnicianDetailOut)
def technician_detail(profile_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Full profile incl. documents, certificates and categories for review."""
    profile = db.get(TechnicianProfile, profile_id)
    if not profile:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Profile not found")
    return _serialize_detail(db, profile)


@router.post("/{profile_id}/review", response_model=TechnicianProfileOut)
def review_technician(
    profile_id: int, payload: TechnicianReviewDecision, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    profile = db.get(TechnicianProfile, profile_id)
    if not profile:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Profile not found")
    tech_user = db.get(User, profile.user_id)
    if payload.approve:
        profile.verification_status = VerificationStatus.approved.value
        profile.approved_at = datetime.now(timezone.utc)
        profile.approved_by = admin.id
        tech_user.role = UserRole.technician.value
        notify(db, tech_user.id, NotificationType.technician_approved, "ช่างได้รับการอนุมัติ", "คุณสามารถรับงานได้แล้ว")
    else:
        profile.verification_status = VerificationStatus.rejected.value
    log_action(db, "technician.review", actor_id=admin.id, entity_type="technician_profile", entity_id=profile.id, detail={"approve": payload.approve, "reason": payload.reason}, request=request)
    db.commit()
    db.refresh(profile)
    return profile
