from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from api.core.db import get_db
from api.core.deps import require_wedding_access
from api.schemas.checklist import (
    BulkCompleteRequest,
    BulkCompleteResult,
    ChecklistCategory,
    ChecklistItemCreate,
    ChecklistItemPublic,
    ChecklistItemUpdate,
    ChecklistPriority,
)

router = APIRouter(prefix="/weddings/{wedding_id}/checklist", tags=["checklist"])


def _get_item_or_404(db: Session, wedding_id: int, item_id: int):
    from app.models import ChecklistItem

    item = db.query(ChecklistItem).filter(ChecklistItem.id == item_id).first()
    if item is None or item.wedding_id != wedding_id:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    return item


# IMPORTANT: /bulk-complete must be registered before /{item_id}
@router.post("/bulk-complete", response_model=BulkCompleteResult)
def bulk_complete(
    body: BulkCompleteRequest,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import ChecklistItem

    q = db.query(ChecklistItem).filter(ChecklistItem.wedding_id == wedding.id)
    if body.category is not None:
        q = q.filter(ChecklistItem.category == body.category.value)

    update_values = {
        ChecklistItem.is_completed: body.completed,
        ChecklistItem.completed_at: datetime.now(UTC) if body.completed else None,
    }
    updated_count = q.update(update_values, synchronize_session=False)
    db.commit()
    return BulkCompleteResult(updated_count=updated_count)


@router.get("", response_model=list[ChecklistItemPublic])
def list_items(
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
    category: Annotated[ChecklistCategory | None, Query()] = None,
    priority: Annotated[ChecklistPriority | None, Query()] = None,
    completed: Annotated[bool | None, Query()] = None,
):
    from app.models import ChecklistItem

    q = db.query(ChecklistItem).filter(ChecklistItem.wedding_id == wedding.id)
    if category is not None:
        q = q.filter(ChecklistItem.category == category.value)
    if priority is not None:
        q = q.filter(ChecklistItem.priority == priority.value)
    if completed is not None:
        q = q.filter(ChecklistItem.is_completed == completed)
    return q.order_by(ChecklistItem.id).all()


@router.post("", response_model=ChecklistItemPublic, status_code=status.HTTP_201_CREATED)
def create_item(
    body: ChecklistItemCreate,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import ChecklistItem

    data = body.model_dump()
    for enum_field in ("category", "priority"):
        if enum_field in data and hasattr(data[enum_field], "value"):
            data[enum_field] = data[enum_field].value
    if data.get("is_completed"):
        data["completed_at"] = datetime.now(UTC)

    item = ChecklistItem(wedding_id=wedding.id, **data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=ChecklistItemPublic)
def get_item(
    item_id: int,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    return _get_item_or_404(db, wedding.id, item_id)


@router.patch("/{item_id}", response_model=ChecklistItemPublic)
def patch_item(
    item_id: int,
    body: ChecklistItemUpdate,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    item = _get_item_or_404(db, wedding.id, item_id)
    update = body.model_dump(exclude_unset=True)
    for enum_field in ("category", "priority"):
        if enum_field in update and hasattr(update[enum_field], "value"):
            update[enum_field] = update[enum_field].value
    if "is_completed" in update:
        update["completed_at"] = datetime.now(UTC) if update["is_completed"] else None
    for field, value in update.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    item = _get_item_or_404(db, wedding.id, item_id)
    db.delete(item)
    db.commit()
    return Response(status_code=204)
