from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from api.core.db import get_db
from api.core.deps import get_current_user, require_wedding_access
from api.schemas.wedding import WeddingCreate, WeddingPublic, WeddingUpdate

router = APIRouter(prefix="/weddings", tags=["weddings"])


@router.get("", response_model=list[WeddingPublic])
def list_weddings(
    current_user: Annotated[object, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """List all weddings owned by the current user."""
    from app.models import Wedding

    return (
        db.query(Wedding)
        .filter(Wedding.user_id == current_user.id)
        .order_by(Wedding.created_at.desc())
        .all()
    )


@router.post(
    "",
    response_model=WeddingPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_wedding(
    wedding_in: WeddingCreate,
    current_user: Annotated[object, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Create a new wedding owned by the current user."""
    from app.models import Wedding

    wedding = Wedding(
        user_id=current_user.id,
        **wedding_in.model_dump(),
    )
    db.add(wedding)
    db.commit()
    db.refresh(wedding)
    return wedding


@router.get("/{wedding_id}", response_model=WeddingPublic)
def get_wedding(
    wedding: Annotated[object, Depends(require_wedding_access)],
):
    """Get a single wedding by ID. 404 if not found or not owned."""
    return wedding


@router.patch("/{wedding_id}", response_model=WeddingPublic)
def update_wedding(
    wedding_in: WeddingUpdate,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update a wedding. PATCH semantics — only provided fields change."""
    update_data = wedding_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(wedding, field, value)
    wedding.updated_at = datetime.now(UTC)
    db.commit()
    db.refresh(wedding)
    return wedding


@router.delete(
    "/{wedding_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_wedding(
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    """Delete a wedding. Cascades to guests, budget, vendors, etc."""
    db.delete(wedding)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
