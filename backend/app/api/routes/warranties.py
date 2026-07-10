"""Warranty claims raised by customers against a previous job."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models.enums import NotificationType, WarrantyClaimStatus
from app.models.health import Warranty, WarrantyClaim
from app.models.job import JobRequest
from app.models.user import User
from app.schemas.records import WarrantyClaimCreate, WarrantyClaimOut
from app.services.audit import log_action
from app.services.notifications import notify

router = APIRouter(prefix="/warranty-claims", tags=["warranty"])


@router.post("", response_model=WarrantyClaimOut, status_code=status.HTTP_201_CREATED)
def create_claim(
    payload: WarrantyClaimCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    job = db.get(JobRequest, payload.original_job_id)
    if not job or job.customer_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Original job not found")
    warranty = db.query(Warranty).filter(Warranty.job_id == job.id).first()
    if not warranty or not warranty.has_warranty:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This job has no active warranty")

    claim = WarrantyClaim(
        original_job_id=job.id,
        customer_id=user.id,
        reason=payload.reason,
        evidence=payload.evidence,
        status=WarrantyClaimStatus.submitted.value,
    )
    db.add(claim)
    log_action(db, "warranty.claim", actor_id=user.id, entity_type="warranty_claim", entity_id=job.id, request=request)
    db.commit()
    db.refresh(claim)
    return claim


@router.get("", response_model=list[WarrantyClaimOut])
def list_claims(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(WarrantyClaim)
    from app.models.enums import UserRole

    if user.role == UserRole.customer.value:
        q = q.filter(WarrantyClaim.customer_id == user.id)
    return q.order_by(WarrantyClaim.id.desc()).all()


@router.post("/{claim_id}/status", response_model=WarrantyClaimOut)
def update_claim(
    claim_id: int, request: Request, new_status: str, resolution: str | None = None,
    admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    claim = db.get(WarrantyClaim, claim_id)
    if not claim:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Claim not found")
    if new_status not in {s.value for s in WarrantyClaimStatus}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid status")
    claim.status = new_status
    if resolution:
        claim.resolution = resolution
    notify(db, claim.customer_id, NotificationType.warranty_claim_update, "อัปเดตการเคลมประกัน", new_status)
    log_action(db, "warranty.update", actor_id=admin.id, entity_type="warranty_claim", entity_id=claim.id, detail={"status": new_status}, request=request)
    db.commit()
    db.refresh(claim)
    return claim
