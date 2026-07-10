"""Customer property and asset management."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.property import Asset, Property
from app.models.user import User
from app.schemas.common import Message
from app.schemas.property import (
    AssetCreate,
    AssetOut,
    AssetUpdate,
    PropertyCreate,
    PropertyOut,
    PropertyUpdate,
)

router = APIRouter(prefix="/properties", tags=["properties"])


def _owned_property(db: Session, property_id: int, user: User) -> Property:
    prop = db.get(Property, property_id)
    if not prop or prop.owner_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Property not found")
    return prop


@router.get("", response_model=list[PropertyOut])
def list_properties(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Property).filter(Property.owner_id == user.id).order_by(Property.id).all()


@router.post("", response_model=PropertyOut, status_code=status.HTTP_201_CREATED)
def create_property(payload: PropertyCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prop = Property(owner_id=user.id, **payload.model_dump())
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


@router.get("/{property_id}", response_model=PropertyOut)
def get_property(property_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _owned_property(db, property_id, user)


@router.patch("/{property_id}", response_model=PropertyOut)
def update_property(
    property_id: int, payload: PropertyUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    prop = _owned_property(db, property_id, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(prop, field, value)
    db.commit()
    db.refresh(prop)
    return prop


@router.delete("/{property_id}", response_model=Message)
def delete_property(property_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prop = _owned_property(db, property_id, user)
    db.delete(prop)
    db.commit()
    return Message(message="Property deleted")


# --- assets ------------------------------------------------------------------

@router.get("/{property_id}/assets", response_model=list[AssetOut])
def list_assets(property_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _owned_property(db, property_id, user)
    return db.query(Asset).filter(Asset.property_id == property_id).order_by(Asset.id).all()


@router.post("/{property_id}/assets", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
def create_asset(
    property_id: int, payload: AssetCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    _owned_property(db, property_id, user)
    asset = Asset(property_id=property_id, **payload.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.patch("/{property_id}/assets/{asset_id}", response_model=AssetOut)
def update_asset(
    property_id: int,
    asset_id: int,
    payload: AssetUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _owned_property(db, property_id, user)
    asset = db.get(Asset, asset_id)
    if not asset or asset.property_id != property_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(asset, field, value)
    db.commit()
    db.refresh(asset)
    return asset


@router.delete("/{property_id}/assets/{asset_id}", response_model=Message)
def delete_asset(
    property_id: int, asset_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    _owned_property(db, property_id, user)
    asset = db.get(Asset, asset_id)
    if not asset or asset.property_id != property_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")
    db.delete(asset)
    db.commit()
    return Message(message="Asset deleted")
