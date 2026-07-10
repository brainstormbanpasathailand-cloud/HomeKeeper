"""Quotation creation by technicians and approval by customers."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.enums import JobStatus, NotificationType, QuotationStatus, UserRole
from app.models.job import JobRequest
from app.models.quotation import Part, Quotation, QuotationItem
from app.models.user import User
from app.schemas.job import QuotationCreate, QuotationDecision, QuotationOut
from app.services.audit import log_action
from app.services.jobs import change_status
from app.services.notifications import notify

router = APIRouter(tags=["quotations"])


def _compute_total(payload: QuotationCreate) -> float:
    items_total = sum(i.quantity * i.unit_price for i in payload.items)
    parts_total = sum(p.quantity * p.unit_price for p in payload.parts)
    subtotal = (
        payload.labor_cost
        + payload.travel_cost
        + payload.inspection_fee
        + payload.emergency_surcharge
        + payload.other_charges
        + items_total
        + parts_total
        + payload.platform_fee
        + payload.vat
        - payload.discount
    )
    return round(subtotal, 2)


@router.post("/jobs/{job_id}/quotations", response_model=QuotationOut, status_code=status.HTTP_201_CREATED)
def create_quotation(
    job_id: int, payload: QuotationCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if user.role != UserRole.technician.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only technicians can create quotations")
    job = db.get(JobRequest, job_id)
    if not job or job.assigned_technician_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found or not assigned to you")

    version = (
        db.query(Quotation).filter(Quotation.job_id == job_id).count() + 1
    )
    quotation = Quotation(
        job_id=job_id,
        technician_id=user.id,
        version=version,
        labor_cost=payload.labor_cost,
        travel_cost=payload.travel_cost,
        inspection_fee=payload.inspection_fee,
        emergency_surcharge=payload.emergency_surcharge,
        other_charges=payload.other_charges,
        discount=payload.discount,
        platform_fee=payload.platform_fee,
        vat=payload.vat,
        total=_compute_total(payload),
        notes=payload.notes,
        valid_until=payload.valid_until,
        status=QuotationStatus.sent.value,
    )
    db.add(quotation)
    db.flush()
    for item in payload.items:
        db.add(
            QuotationItem(
                quotation_id=quotation.id,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                amount=round(item.quantity * item.unit_price, 2),
            )
        )
    for part in payload.parts:
        db.add(Part(quotation_id=quotation.id, job_id=job_id, **part.model_dump()))

    if job.status != JobStatus.quoted.value:
        change_status(db, job, JobStatus.quoted.value, actor_id=user.id, force=True)
    notify(db, job.customer_id, NotificationType.quotation_created, "มีใบเสนอราคาใหม่", f"งาน {job.job_number}")
    log_action(db, "quotation.create", actor_id=user.id, entity_type="quotation", entity_id=quotation.id, request=request)
    db.commit()
    db.refresh(quotation)
    return quotation


@router.get("/jobs/{job_id}/quotations", response_model=list[QuotationOut])
def list_quotations(job_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.get(JobRequest, job_id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    is_admin = user.role in {UserRole.admin.value, UserRole.super_admin.value, UserRole.dispatcher.value}
    if not (is_admin or job.customer_id == user.id or job.assigned_technician_id == user.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed")
    return db.query(Quotation).filter(Quotation.job_id == job_id).order_by(Quotation.version).all()


@router.post("/quotations/{quotation_id}/decision", response_model=QuotationOut)
def decide_quotation(
    quotation_id: int, payload: QuotationDecision, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    quotation = db.get(Quotation, quotation_id)
    if not quotation:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Quotation not found")
    job = db.get(JobRequest, quotation.job_id)
    if job.customer_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the customer can decide")
    if quotation.status not in {QuotationStatus.sent.value, QuotationStatus.revision_requested.value}:
        raise HTTPException(status.HTTP_409_CONFLICT, "Quotation is not awaiting a decision")

    from datetime import datetime, timezone

    quotation.responded_at = datetime.now(timezone.utc)
    quotation.customer_response_note = payload.note

    if payload.decision == "approve":
        quotation.status = QuotationStatus.approved.value
        change_status(db, job, JobStatus.approved.value, actor_id=user.id, force=True)
        notify(db, job.assigned_technician_id, NotificationType.quotation_approved, "ลูกค้าอนุมัติใบเสนอราคา", f"งาน {job.job_number}")
    elif payload.decision == "reject":
        quotation.status = QuotationStatus.rejected.value
    else:  # revision
        quotation.status = QuotationStatus.revision_requested.value
        change_status(db, job, JobStatus.quotation_revision_requested.value, actor_id=user.id, force=True)

    log_action(db, "quotation.decision", actor_id=user.id, entity_type="quotation", entity_id=quotation.id, detail={"decision": payload.decision}, request=request)
    db.commit()
    db.refresh(quotation)
    return quotation
