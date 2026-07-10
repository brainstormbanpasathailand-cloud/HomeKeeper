"""Job lifecycle: status machine, job number generation, health record
generation on completion, and warranty creation."""
from datetime import date, timedelta
from typing import Optional

from fastapi import HTTPException, status as http_status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.enums import JobStatus, MediaKind, NotificationType
from app.models.health import HealthRecord, Warranty
from app.models.job import JobMedia, JobRequest, JobStatusHistory
from app.models.quotation import Part, Quotation
from app.services.notifications import notify

# Allowed status transitions. Roles are enforced at the route layer; this map
# guards that the workflow itself only moves in valid directions.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    JobStatus.draft.value: {JobStatus.requested.value, JobStatus.cancelled.value},
    JobStatus.requested.value: {
        JobStatus.reviewing.value,
        JobStatus.searching.value,
        JobStatus.assigned.value,
        JobStatus.cancelled.value,
    },
    JobStatus.reviewing.value: {
        JobStatus.searching.value,
        JobStatus.assigned.value,
        JobStatus.cancelled.value,
    },
    JobStatus.searching.value: {JobStatus.assigned.value, JobStatus.cancelled.value},
    JobStatus.assigned.value: {
        JobStatus.accepted.value,
        JobStatus.rejected.value,
        JobStatus.cancelled.value,
    },
    JobStatus.rejected.value: {JobStatus.assigned.value, JobStatus.searching.value, JobStatus.cancelled.value},
    JobStatus.accepted.value: {JobStatus.traveling.value, JobStatus.cancelled.value},
    JobStatus.traveling.value: {JobStatus.arrived.value, JobStatus.cancelled.value},
    JobStatus.arrived.value: {JobStatus.inspecting.value, JobStatus.cancelled.value},
    JobStatus.inspecting.value: {JobStatus.quoted.value, JobStatus.in_progress.value, JobStatus.cancelled.value},
    JobStatus.quoted.value: {
        JobStatus.approved.value,
        JobStatus.quotation_revision_requested.value,
        JobStatus.cancelled.value,
    },
    JobStatus.quotation_revision_requested.value: {JobStatus.quoted.value, JobStatus.cancelled.value},
    JobStatus.approved.value: {JobStatus.in_progress.value, JobStatus.cancelled.value},
    JobStatus.in_progress.value: {JobStatus.paused.value, JobStatus.completed.value, JobStatus.cancelled.value},
    JobStatus.paused.value: {JobStatus.in_progress.value, JobStatus.cancelled.value},
    JobStatus.completed.value: {JobStatus.customer_confirmed.value, JobStatus.disputed.value},
    JobStatus.customer_confirmed.value: {JobStatus.closed.value, JobStatus.disputed.value},
    JobStatus.disputed.value: {JobStatus.closed.value, JobStatus.in_progress.value},
    JobStatus.warranty_claim.value: {JobStatus.in_progress.value, JobStatus.closed.value},
    JobStatus.cancelled.value: set(),
    JobStatus.closed.value: set(),
}


def generate_job_number(db: Session) -> str:
    year = date.today().year
    count = db.query(func.count(JobRequest.id)).scalar() or 0
    return f"HK-{year}-{count + 1:06d}"


def can_transition(current: str, target: str) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, set())


def change_status(
    db: Session,
    job: JobRequest,
    target: str,
    actor_id: Optional[int] = None,
    note: Optional[str] = None,
    force: bool = False,
) -> JobRequest:
    if target not in {s.value for s in JobStatus}:
        raise HTTPException(http_status.HTTP_400_BAD_REQUEST, f"Unknown status '{target}'")
    if not force and job.status != target and not can_transition(job.status, target):
        raise HTTPException(
            http_status.HTTP_409_CONFLICT,
            f"Cannot move job from '{job.status}' to '{target}'",
        )
    previous = job.status
    job.status = target
    db.add(
        JobStatusHistory(
            job_id=job.id, from_status=previous, to_status=target, changed_by=actor_id, note=note
        )
    )

    # Side effects on terminal / notable states.
    if target == JobStatus.completed.value:
        _on_completed(db, job)
    return job


def _on_completed(db: Session, job: JobRequest) -> None:
    """When a job completes, auto-generate the Home Health Record + Warranty
    if one does not already exist."""
    existing = db.query(HealthRecord).filter(HealthRecord.job_id == job.id).first()
    if existing:
        return

    quotation = (
        db.query(Quotation)
        .filter(Quotation.job_id == job.id, Quotation.status == "approved")
        .order_by(Quotation.version.desc())
        .first()
    )
    # A part may carry both job_id and quotation_id (the quotation route sets
    # both), so de-duplicate by primary key to avoid double-counting.
    parts_by_id: dict[int, Part] = {p.id: p for p in db.query(Part).filter(Part.job_id == job.id).all()}
    if quotation:
        for p in db.query(Part).filter(Part.quotation_id == quotation.id).all():
            parts_by_id[p.id] = p
    parts = list(parts_by_id.values())

    before = [m.url for m in job.media if m.kind == MediaKind.before.value]
    after = [m.url for m in job.media if m.kind == MediaKind.after.value]

    labor = float(quotation.labor_cost) if quotation else None
    parts_cost = sum(float(p.unit_price) * float(p.quantity) for p in parts) if parts else None
    total = float(quotation.total) if quotation else None

    record = HealthRecord(
        property_id=job.property_id,
        asset_id=job.asset_id,
        job_id=job.id,
        customer_id=job.customer_id,
        service_date=date.today(),
        issue=job.title,
        diagnosis=job.problem_description,
        work_performed=quotation.notes if quotation else None,
        technician_id=job.assigned_technician_id,
        parts_used=[
            {
                "part_name": p.part_name,
                "brand": p.brand,
                "quantity": float(p.quantity),
                "authenticity": p.authenticity,
            }
            for p in parts
        ],
        labor_cost=labor,
        parts_cost=parts_cost,
        total_cost=total,
        before_photos=before,
        after_photos=after,
    )
    db.add(record)
    db.flush()

    # Default warranty: 30 days covering labor. Editable by admin/technician.
    warranty_days = 30
    start = date.today()
    warranty = Warranty(
        job_id=job.id,
        health_record_id=record.id,
        has_warranty=True,
        warranty_days=warranty_days,
        covers_labor=True,
        covers_parts=bool(parts),
        start_date=start,
        end_date=start + timedelta(days=warranty_days),
    )
    db.add(warranty)
    record.warranty_start = warranty.start_date
    record.warranty_end = warranty.end_date

    notify(
        db,
        job.customer_id,
        NotificationType.job_completed,
        title="งานเสร็จสมบูรณ์ / Job completed",
        body=f"งาน {job.job_number} เสร็จแล้ว ระบบได้บันทึกประวัติการดูแลบ้านให้อัตโนมัติ",
        data={"job_id": job.id, "health_record_id": record.id},
    )
