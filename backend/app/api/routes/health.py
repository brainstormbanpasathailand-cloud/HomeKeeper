"""Home Health Record read endpoints (timeline, per-asset, cost summary)."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.enums import UserRole
from app.models.health import HealthRecord
from app.models.user import User
from app.schemas.records import HealthRecordOut

router = APIRouter(prefix="/health-records", tags=["health-records"])


def _visible(db: Session, user: User):
    q = db.query(HealthRecord)
    if user.role == UserRole.customer.value:
        q = q.filter(HealthRecord.customer_id == user.id)
    elif user.role == UserRole.technician.value:
        q = q.filter(HealthRecord.technician_id == user.id)
    return q


@router.get("", response_model=list[HealthRecordOut])
def list_records(
    property_id: int | None = Query(None),
    asset_id: int | None = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = _visible(db, user)
    if property_id:
        q = q.filter(HealthRecord.property_id == property_id)
    if asset_id:
        q = q.filter(HealthRecord.asset_id == asset_id)
    return q.order_by(HealthRecord.service_date.desc(), HealthRecord.id.desc()).all()


@router.get("/summary")
def cost_summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = _visible(db, user).all()
    total = sum(float(r.total_cost or 0) for r in records)
    by_year: dict[int, float] = {}
    for r in records:
        if r.service_date:
            by_year[r.service_date.year] = by_year.get(r.service_date.year, 0) + float(r.total_cost or 0)
    return {"total_spent": round(total, 2), "records": len(records), "by_year": by_year}


@router.get("/{record_id}", response_model=HealthRecordOut)
def get_record(record_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.get(HealthRecord, record_id)
    if not record:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Record not found")
    is_admin = user.role in {UserRole.admin.value, UserRole.super_admin.value, UserRole.support.value}
    if not (is_admin or record.customer_id == user.id or record.technician_id == user.id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed")
    return record
