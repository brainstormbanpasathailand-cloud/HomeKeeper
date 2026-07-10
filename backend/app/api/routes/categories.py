"""Service categories: public read; admin create/update/close/reorder."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin
from app.models.catalog import ServiceCategory
from app.models.user import User
from app.schemas.catalog import (
    ReorderRequest,
    ServiceCategoryCreate,
    ServiceCategoryOut,
    ServiceCategoryUpdate,
)
from app.schemas.common import Message
from app.services.audit import log_action

router = APIRouter(prefix="/service-categories", tags=["service-categories"])


@router.get("", response_model=list[ServiceCategoryOut])
def list_categories(include_inactive: bool = Query(False), db: Session = Depends(get_db)):
    q = db.query(ServiceCategory)
    if not include_inactive:
        q = q.filter(ServiceCategory.is_active == True)  # noqa: E712
    return q.order_by(ServiceCategory.sort_order, ServiceCategory.id).all()


@router.post("", response_model=ServiceCategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: ServiceCategoryCreate, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    if db.query(ServiceCategory).filter(ServiceCategory.slug == payload.slug).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Slug already exists")
    category = ServiceCategory(**payload.model_dump())
    db.add(category)
    log_action(db, "category.create", actor_id=admin.id, entity_type="service_category", detail={"slug": payload.slug}, request=request)
    db.commit()
    db.refresh(category)
    return category


@router.patch("/{category_id}", response_model=ServiceCategoryOut)
def update_category(
    category_id: int, payload: ServiceCategoryUpdate, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    category = db.get(ServiceCategory, category_id)
    if not category:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    log_action(db, "category.update", actor_id=admin.id, entity_type="service_category", entity_id=category_id, request=request)
    db.commit()
    db.refresh(category)
    return category


@router.post("/{category_id}/close", response_model=Message)
def close_category(
    category_id: int, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    category = db.get(ServiceCategory, category_id)
    if not category:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    category.is_active = False
    log_action(db, "category.close", actor_id=admin.id, entity_type="service_category", entity_id=category_id, request=request)
    db.commit()
    return Message(message="Category closed")


@router.post("/reorder", response_model=Message)
def reorder_categories(
    payload: ReorderRequest, request: Request, admin: User = Depends(require_admin), db: Session = Depends(get_db)
):
    for order, cid in enumerate(payload.ordered_ids):
        category = db.get(ServiceCategory, cid)
        if category:
            category.sort_order = order
    log_action(db, "category.reorder", actor_id=admin.id, request=request)
    db.commit()
    return Message(message="Reordered")
