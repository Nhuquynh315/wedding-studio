from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from api.core.db import get_db
from api.core.deps import require_wedding_access
from api.schemas.vendor import VendorCreate, VendorPublic, VendorStatus, VendorUpdate

router = APIRouter(prefix="/weddings/{wedding_id}/vendors", tags=["vendors"])


def _get_vendor_or_404(db: Session, wedding_id: int, vendor_id: int):
    from app.models import Vendor

    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if vendor is None or vendor.wedding_id != wedding_id:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.get("", response_model=list[VendorPublic])
def list_vendors(
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: Annotated[VendorStatus | None, Query(alias="status")] = None,
):
    from app.models import Vendor

    q = db.query(Vendor).filter(Vendor.wedding_id == wedding.id)
    if status_filter is not None:
        q = q.filter(Vendor.status == status_filter.value)
    return q.order_by(Vendor.id).all()


@router.post("", response_model=VendorPublic, status_code=status.HTTP_201_CREATED)
def create_vendor(
    body: VendorCreate,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import Vendor

    data = body.model_dump()
    if "status" in data and hasattr(data["status"], "value"):
        data["status"] = data["status"].value

    vendor = Vendor(wedding_id=wedding.id, **data)
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


@router.get("/{vendor_id}", response_model=VendorPublic)
def get_vendor(
    vendor_id: int,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    return _get_vendor_or_404(db, wedding.id, vendor_id)


@router.patch("/{vendor_id}", response_model=VendorPublic)
def patch_vendor(
    vendor_id: int,
    body: VendorUpdate,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    vendor = _get_vendor_or_404(db, wedding.id, vendor_id)
    update = body.model_dump(exclude_unset=True)
    if "status" in update and hasattr(update["status"], "value"):
        update["status"] = update["status"].value
    for field, value in update.items():
        setattr(vendor, field, value)
    db.commit()
    db.refresh(vendor)
    return vendor


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor(
    vendor_id: int,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    """Delete a vendor. Manually nullifies vendor_id on associated expenses
    before deleting the vendor itself.

    The model FK doesn't have ON DELETE SET NULL configured, so we enforce
    SET NULL semantics at the application layer. Documented in CLAUDE.md as
    known debt — the DB-level constraint should be added in Phase 5 when
    migrating to Postgres.
    """
    from app.models import Expense

    vendor = _get_vendor_or_404(db, wedding.id, vendor_id)

    db.query(Expense).filter(Expense.vendor_id == vendor.id).update(
        {Expense.vendor_id: None},
        synchronize_session="fetch",
    )
    db.delete(vendor)
    db.commit()
    return Response(status_code=204)
