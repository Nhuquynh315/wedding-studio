from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.core.db import get_db
from api.core.deps import require_wedding_access
from api.schemas.guest import GuestCreate, GuestPublic, GuestUpdate

router = APIRouter(prefix="/weddings/{wedding_id}/guests", tags=["guests"])


@router.get("", response_model=list[GuestPublic])
def list_guests(
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import Guest

    return db.query(Guest).filter(Guest.wedding_id == wedding.id).all()


@router.post("", response_model=GuestPublic, status_code=status.HTTP_201_CREATED)
def create_guest(
    body: GuestCreate,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import Guest

    guest = Guest(wedding_id=wedding.id, **body.model_dump())
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return guest


@router.get("/{guest_id}", response_model=GuestPublic)
def get_guest(
    guest_id: int,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import Guest

    guest = db.query(Guest).filter(Guest.id == guest_id, Guest.wedding_id == wedding.id).first()
    if guest is None:
        raise HTTPException(status_code=404, detail="Guest not found")
    return guest


@router.patch("/{guest_id}", response_model=GuestPublic)
def patch_guest(
    guest_id: int,
    body: GuestUpdate,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import Guest

    guest = db.query(Guest).filter(Guest.id == guest_id, Guest.wedding_id == wedding.id).first()
    if guest is None:
        raise HTTPException(status_code=404, detail="Guest not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(guest, field, value)
    db.commit()
    db.refresh(guest)
    return guest


@router.delete("/{guest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_guest(
    guest_id: int,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import Guest

    guest = db.query(Guest).filter(Guest.id == guest_id, Guest.wedding_id == wedding.id).first()
    if guest is None:
        raise HTTPException(status_code=404, detail="Guest not found")
    db.delete(guest)
    db.commit()
