"""Job requests and the customer + technician workflow."""
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.pagination import PageParams, paginate
from app.database import get_db
from app.deps import get_current_user
from app.models.enums import AssignmentStatus, JobStatus, NotificationType, UserRole
from app.models.catalog import ServiceCategory
from app.models.job import JobAssignment, JobMedia, JobRequest
from app.models.user import User
from app.schemas.common import Message, Page
from app.schemas.job import (
    AssignmentResponse,
    JobCreate,
    JobMediaCreate,
    JobOut,
    StatusUpdateRequest,
)
from app.services.audit import log_action
from app.services.jobs import change_status, generate_job_number
from app.services.notifications import notify

router = APIRouter(prefix="/jobs", tags=["jobs"])

# Which target statuses a technician is permitted to drive.
TECH_ALLOWED = {
    JobStatus.traveling.value,
    JobStatus.arrived.value,
    JobStatus.inspecting.value,
    JobStatus.in_progress.value,
    JobStatus.paused.value,
    JobStatus.completed.value,
}
CUSTOMER_ALLOWED = {JobStatus.customer_confirmed.value, JobStatus.cancelled.value, JobStatus.disputed.value}


def _get_job_for_actor(db: Session, job_id: int, user: User) -> JobRequest:
    job = db.get(JobRequest, job_id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    is_admin = user.role in {UserRole.admin.value, UserRole.super_admin.value, UserRole.dispatcher.value, UserRole.support.value}
    if not (is_admin or job.customer_id == user.id or job.assigned_technician_id == user.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed to access this job")
    return job


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if idempotency_key:
        existing = (
            db.query(JobRequest)
            .filter(JobRequest.customer_id == user.id, JobRequest.idempotency_key == idempotency_key)
            .first()
        )
        if existing:
            return existing

    category = db.get(ServiceCategory, payload.service_category_id)
    if not category or not category.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid service category")

    job = JobRequest(
        job_number=generate_job_number(db),
        customer_id=user.id,
        idempotency_key=idempotency_key,
        status=JobStatus.requested.value,
        **payload.model_dump(),
    )
    db.add(job)
    db.flush()
    log_action(db, "job.create", actor_id=user.id, entity_type="job", entity_id=job.id, request=request)
    db.commit()
    db.refresh(job)
    return job


@router.get("", response_model=Page[JobOut])
def list_jobs(
    params: PageParams = Depends(),
    status_filter: str | None = Query(None, alias="status"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(JobRequest)
    if user.role == UserRole.customer.value:
        q = q.filter(JobRequest.customer_id == user.id)
    elif user.role == UserRole.technician.value:
        q = q.filter(JobRequest.assigned_technician_id == user.id)
    # admin/dispatcher/support see all
    if status_filter:
        q = q.filter(JobRequest.status == status_filter)
    q = q.order_by(JobRequest.id.desc())
    return paginate(q, params)


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_job_for_actor(db, job_id, user)


@router.post("/{job_id}/status", response_model=JobOut)
def update_status(
    job_id: int,
    payload: StatusUpdateRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = _get_job_for_actor(db, job_id, user)
    role = user.role
    is_admin = role in {UserRole.admin.value, UserRole.super_admin.value, UserRole.dispatcher.value}

    if role == UserRole.technician.value:
        if job.assigned_technician_id != user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not your job")
        if payload.status not in TECH_ALLOWED:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Technicians cannot set this status")
        # Guard: cannot start chargeable work before quotation approved.
        if payload.status == JobStatus.in_progress.value and job.status not in {
            JobStatus.approved.value,
            JobStatus.inspecting.value,
            JobStatus.paused.value,
        }:
            raise HTTPException(status.HTTP_409_CONFLICT, "Quotation must be approved before starting work")
    elif role == UserRole.customer.value:
        if job.customer_id != user.id or payload.status not in CUSTOMER_ALLOWED:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Customers cannot set this status")
    elif not is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed")

    change_status(db, job, payload.status, actor_id=user.id, note=payload.note, force=is_admin)

    # Notify the counterparty on notable transitions.
    if payload.status in {JobStatus.traveling.value, JobStatus.arrived.value}:
        nt = NotificationType.technician_traveling if payload.status == JobStatus.traveling.value else NotificationType.technician_arrived
        notify(db, job.customer_id, nt, "อัปเดตสถานะงาน", f"งาน {job.job_number}: {payload.status}")
    log_action(db, "job.status", actor_id=user.id, entity_type="job", entity_id=job.id, detail={"status": payload.status}, request=request)
    db.commit()
    db.refresh(job)
    return job


@router.post("/{job_id}/respond", response_model=JobOut)
def respond_assignment(
    job_id: int,
    payload: AssignmentResponse,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Technician accepts or rejects an offered assignment."""
    if user.role != UserRole.technician.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only technicians can respond")
    job = db.get(JobRequest, job_id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    assignment = (
        db.query(JobAssignment)
        .filter(
            JobAssignment.job_id == job_id,
            JobAssignment.technician_id == user.id,
            JobAssignment.status == AssignmentStatus.offered.value,
        )
        .order_by(JobAssignment.id.desc())
        .first()
    )
    if not assignment:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No pending assignment for you")

    from datetime import datetime, timezone

    assignment.responded_at = datetime.now(timezone.utc)
    if payload.accept:
        assignment.status = AssignmentStatus.accepted.value
        change_status(db, job, JobStatus.accepted.value, actor_id=user.id, note=payload.note)
        notify(db, job.customer_id, NotificationType.job_accepted, "ช่างรับงานแล้ว", f"งาน {job.job_number}")
    else:
        assignment.status = AssignmentStatus.rejected.value
        job.assigned_technician_id = None
        change_status(db, job, JobStatus.searching.value, actor_id=user.id, note=payload.note, force=True)
    log_action(db, "job.respond", actor_id=user.id, entity_type="job", entity_id=job.id, detail={"accept": payload.accept}, request=request)
    db.commit()
    db.refresh(job)
    return job


@router.post("/{job_id}/media", response_model=Message, status_code=status.HTTP_201_CREATED)
def add_media(
    job_id: int,
    payload: JobMediaCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = _get_job_for_actor(db, job_id, user)
    db.add(JobMedia(job_id=job.id, uploaded_by=user.id, kind=payload.kind, url=payload.url, caption=payload.caption))
    db.commit()
    return Message(message="Media added")
