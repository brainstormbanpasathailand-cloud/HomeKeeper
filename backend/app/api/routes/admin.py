"""Admin & dispatcher endpoints: dashboard, user management, job dispatch."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.pagination import PageParams, paginate
from app.database import get_db
from app.deps import require_admin, require_super_admin
from app.models.enums import (
    AssignmentStatus,
    JobStatus,
    NotificationType,
    OnlineStatus,
    UserRole,
    VerificationStatus,
)
from app.models.job import JobAssignment, JobRequest
from app.models.misc import AuditLog
from app.models.technician import TechnicianProfile
from app.models.user import User
from app.schemas.auth import UserOut
from app.schemas.common import Message, Page
from app.schemas.job import AssignRequest, JobOut
from app.services.audit import log_action
from app.services.jobs import change_status
from app.services.notifications import notify

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard")
def dashboard(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    def count(status_value: str) -> int:
        return db.query(func.count(JobRequest.id)).filter(JobRequest.status == status_value).scalar() or 0

    return {
        "new_jobs": count(JobStatus.requested.value),
        "searching_jobs": count(JobStatus.searching.value),
        "in_progress_jobs": count(JobStatus.in_progress.value),
        "disputed_jobs": count(JobStatus.disputed.value),
        "completed_jobs": count(JobStatus.completed.value),
        "urgent_jobs": db.query(func.count(JobRequest.id)).filter(JobRequest.urgency == "emergency", JobRequest.status.in_([JobStatus.requested.value, JobStatus.searching.value])).scalar() or 0,
        "technicians_pending_review": db.query(func.count(TechnicianProfile.id)).filter(TechnicianProfile.verification_status.in_([VerificationStatus.submitted.value, VerificationStatus.under_review.value])).scalar() or 0,
        "technicians_online": db.query(func.count(TechnicianProfile.id)).filter(TechnicianProfile.online_status == OnlineStatus.online.value).scalar() or 0,
        "total_users": db.query(func.count(User.id)).scalar() or 0,
    }


@router.get("/users", response_model=Page[UserOut])
def list_users(
    params: PageParams = Depends(),
    role: str | None = Query(None),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    return paginate(q.order_by(User.id.desc()), params)


@router.post("/users/{user_id}/suspend", response_model=Message)
def suspend_user(
    user_id: int, request: Request, suspend: bool = True, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if target.role == UserRole.super_admin.value:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Cannot suspend a super admin")
    target.is_suspended = suspend
    log_action(db, "admin.suspend_user", actor_id=admin.id, entity_type="user", entity_id=user_id, detail={"suspend": suspend}, request=request)
    db.commit()
    return Message(message="User suspended" if suspend else "User reinstated")


@router.post("/users/{user_id}/role", response_model=UserOut)
def set_role(
    user_id: int, role: str, request: Request, admin: User = Depends(require_super_admin), db: Session = Depends(get_db)
):
    if role not in {r.value for r in UserRole}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid role")
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    target.role = role
    log_action(db, "admin.set_role", actor_id=admin.id, entity_type="user", entity_id=user_id, detail={"role": role}, request=request)
    db.commit()
    db.refresh(target)
    return target


@router.post("/jobs/{job_id}/assign", response_model=JobOut)
def assign_job(
    job_id: int, payload: AssignRequest, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    job = db.get(JobRequest, job_id)
    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    tech = db.get(User, payload.technician_id)
    if not tech or tech.role != UserRole.technician.value:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Target user is not an approved technician")

    # Supersede any prior offer.
    db.query(JobAssignment).filter(
        JobAssignment.job_id == job_id, JobAssignment.status == AssignmentStatus.offered.value
    ).update({"status": AssignmentStatus.reassigned.value})

    db.add(JobAssignment(job_id=job_id, technician_id=tech.id, assigned_by=admin.id, status=AssignmentStatus.offered.value, note=payload.note))
    job.assigned_technician_id = tech.id
    change_status(db, job, JobStatus.assigned.value, actor_id=admin.id, force=True)
    notify(db, tech.id, NotificationType.new_job, "มีงานใหม่มอบหมายให้คุณ", f"งาน {job.job_number}")
    log_action(db, "job.assign", actor_id=admin.id, entity_type="job", entity_id=job.id, detail={"technician_id": tech.id}, request=request)
    db.commit()
    db.refresh(job)
    return job


@router.get("/audit-logs")
def audit_logs(
    params: PageParams = Depends(), admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    q = db.query(AuditLog).order_by(AuditLog.id.desc())
    page = paginate(q, params)
    return {
        "total": page.total,
        "page": page.page,
        "items": [
            {
                "id": a.id,
                "actor_id": a.actor_id,
                "action": a.action,
                "entity_type": a.entity_type,
                "entity_id": a.entity_id,
                "detail": a.detail,
                "created_at": a.created_at,
            }
            for a in page.items
        ],
    }
