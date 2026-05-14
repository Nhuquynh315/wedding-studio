from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload

from api.core.db import get_db
from api.core.deps import require_wedding_access
from api.schemas.seating import (
    WeddingTableCreate,
    WeddingTablePublic,
    WeddingTableUpdate,
    WeddingTableWithGuests,
)

router = APIRouter(prefix="/weddings/{wedding_id}/tables", tags=["seating"])


def _get_table_or_404(db: Session, wedding_id: int, table_id: int):
    from app.models import WeddingTable

    table = db.query(WeddingTable).filter(WeddingTable.id == table_id).first()
    if table is None or table.wedding_id != wedding_id:
        raise HTTPException(status_code=404, detail="Table not found")
    return table


# IMPORTANT: /with-guests must be declared before /{table_id}
@router.get("/with-guests", response_model=list[WeddingTableWithGuests])
def list_tables_with_guests(
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    """List all tables with their assigned guests embedded — for the seating UI."""
    from app.models import WeddingTable

    tables = (
        db.query(WeddingTable)
        .filter(WeddingTable.wedding_id == wedding.id)
        .options(joinedload(WeddingTable.guests))
        .order_by(WeddingTable.id)
        .all()
    )
    return tables


@router.get("", response_model=list[WeddingTablePublic])
def list_tables(
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import WeddingTable

    return (
        db.query(WeddingTable)
        .filter(WeddingTable.wedding_id == wedding.id)
        .order_by(WeddingTable.id)
        .all()
    )


@router.post("", response_model=WeddingTablePublic, status_code=status.HTTP_201_CREATED)
def create_table(
    body: WeddingTableCreate,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import WeddingTable

    table = WeddingTable(wedding_id=wedding.id, **body.model_dump())
    db.add(table)
    db.commit()
    db.refresh(table)
    return table


@router.get("/{table_id}", response_model=WeddingTablePublic)
def get_table(
    table_id: int,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    return _get_table_or_404(db, wedding.id, table_id)


@router.patch("/{table_id}", response_model=WeddingTablePublic)
def patch_table(
    table_id: int,
    body: WeddingTableUpdate,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    table = _get_table_or_404(db, wedding.id, table_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(table, field, value)
    db.commit()
    db.refresh(table)
    return table


@router.delete("/{table_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_table(
    table_id: int,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    """Delete a table. Manually nullifies guest.table_id before deleting (application-level
    SET NULL — model FK lacks ondelete='SET NULL'; deferred to Phase 5)."""
    from app.models import Guest

    table = _get_table_or_404(db, wedding.id, table_id)
    db.query(Guest).filter(Guest.table_id == table.id).update(
        {Guest.table_id: None},
        synchronize_session="fetch",
    )
    db.delete(table)
    db.commit()
    return Response(status_code=204)
