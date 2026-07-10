"""Customer reviews after job completion and admin moderation."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models.enums import JobStatus, UserRole
from app.models.job import JobRequest
from app.models.misc import Review
from app.models.technician import TechnicianProfile
from app.models.user import User
from app.schemas.common import Message
from app.schemas.records import ReviewCreate, ReviewOut
from app.services.audit import log_action

router = APIRouter(tags=["reviews"])

RATING_FIELDS = [
    "rating_quality",
    "rating_punctuality",
    "rating_politeness",
    "rating_cleanliness",
    "rating_value",
    "rating_communication",
]


@router.post("/jobs/{job_id}/review", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
    job_id: int, payload: ReviewCreate, request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    job = db.get(JobRequest, job_id)
    if not job or job.customer_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    if job.status not in {JobStatus.completed.value, JobStatus.customer_confirmed.value, JobStatus.closed.value}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Can only review completed jobs")
    if db.query(Review).filter(Review.job_id == job_id, Review.customer_id == user.id).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Already reviewed")

    data = payload.model_dump()
    ratings = [data[f] for f in RATING_FIELDS if data.get(f) is not None]
    overall = round(sum(ratings) / len(ratings), 2) if ratings else None
    review = Review(
        job_id=job_id,
        customer_id=user.id,
        technician_id=job.assigned_technician_id,
        overall_rating=overall,
        **data,
    )
    db.add(review)
    db.flush()

    # Recompute technician average rating.
    if job.assigned_technician_id:
        profile = db.query(TechnicianProfile).filter(TechnicianProfile.user_id == job.assigned_technician_id).first()
        if profile:
            rows = db.query(Review).filter(Review.technician_id == job.assigned_technician_id, Review.overall_rating.isnot(None)).all()
            if rows:
                profile.average_rating = round(sum(float(r.overall_rating) for r in rows) / len(rows), 2)
    log_action(db, "review.create", actor_id=user.id, entity_type="review", entity_id=review.id, request=request)
    db.commit()
    db.refresh(review)
    return review


@router.get("/technicians/{technician_id}/reviews", response_model=list[ReviewOut])
def technician_reviews(technician_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Review)
        .filter(Review.technician_id == technician_id, Review.is_hidden == False)  # noqa: E712
        .order_by(Review.id.desc())
        .all()
    )


@router.post("/reviews/{review_id}/flag", response_model=Message)
def flag_review(review_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    review.is_flagged = True
    db.commit()
    return Message(message="Review flagged for moderation")


@router.post("/reviews/{review_id}/moderate", response_model=Message)
def moderate_review(
    review_id: int, hide: bool, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found")
    review.is_hidden = hide
    review.is_flagged = False
    log_action(db, "review.moderate", actor_id=admin.id, entity_type="review", entity_id=review.id, detail={"hidden": hide}, request=request)
    db.commit()
    return Message(message="Review moderated")
