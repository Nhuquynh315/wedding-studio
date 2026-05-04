from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.core.db import get_db
from api.core.deps import require_wedding_access
from api.core.pagination import cursor_or_422, encode_cursor
from api.schemas.guest import (
    BulkRSVPResult,
    BulkRSVPUpdate,
    GuestCreate,
    GuestList,
    GuestPublic,
    GuestUpdate,
    RSVPStatus,
)

router = APIRouter(prefix="/weddings/{wedding_id}/guests", tags=["guests"])


@router.get("", response_model=GuestList)
def list_guests(
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    rsvp: Annotated[RSVPStatus | None, Query()] = None,
):
    from app.models import Guest

    last_id = cursor_or_422(cursor)

    q = db.query(Guest).filter(Guest.wedding_id == wedding.id)
    if rsvp is not None:
        q = q.filter(Guest.rsvp_status == rsvp.value)
    if last_id is not None:
        q = q.filter(Guest.id > last_id)

    rows = q.order_by(Guest.id.asc()).limit(limit + 1).all()

    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = encode_cursor(items[-1].id) if has_more and items else None

    return GuestList(items=items, next_cursor=next_cursor, limit=limit)


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


@router.post("/bulk-rsvp", response_model=BulkRSVPResult)
def bulk_update_rsvp(
    body: BulkRSVPUpdate,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import Guest

    q = db.query(Guest).filter(Guest.wedding_id == wedding.id)
    if body.group_name is not None:
        q = q.filter(Guest.group_name == body.group_name)

    updated_count = q.update(
        {Guest.rsvp_status: body.rsvp_status.value},
        synchronize_session=False,
    )
    db.commit()

    return BulkRSVPResult(updated_count=updated_count)


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
