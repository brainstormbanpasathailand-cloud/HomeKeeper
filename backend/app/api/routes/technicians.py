"""Technician onboarding and admin verification."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models.enums import NotificationType, UserRole, VerificationStatus
from app.models.technician import TechnicianProfile, TechnicianServiceCategory
from app.models.user import User
from app.schemas.common import Message
from app.schemas.records import (
    TechnicianApplyRequest,
    TechnicianProfileOut,
    TechnicianReviewDecision,
)
from app.services.audit import log_action
from app.services.notifications import notify

router = APIRouter(prefix="/technicians", tags=["technicians"])


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
        province=payload.province,
        district=payload.district,
        latitude=payload.latitude,
        longitude=payload.longitude,
        service_radius_km=payload.service_radius_km or 10.0,
        years_of_experience=payload.years_of_experience,
        languages=payload.languages,
        bio=payload.bio,
        verification_status=VerificationStatus.submitted.value,
    )
    db.add(profile)
    db.flush()
    for cid in payload.category_ids or []:
        db.add(TechnicianServiceCategory(technician_id=profile.id, service_category_id=cid))
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
