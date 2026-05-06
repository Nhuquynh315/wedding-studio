from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.core.db import get_db
from api.core.deps import require_wedding_access
from api.schemas.budget import (
    BudgetCategoryCreate,
    BudgetCategoryPublic,
    BudgetCategoryUpdate,
    BudgetSummary,
    CategorySummary,
    ExpenseCreate,
    ExpensePublic,
    ExpenseUpdate,
    ScaleBudgetRequest,
    ScaleBudgetResult,
)
from api.services.budget_seeding import scale_categories

router = APIRouter(prefix="/weddings/{wedding_id}/budget", tags=["budget"])


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_category_or_404(db: Session, wedding_id: int, category_id: int):
    from app.models import BudgetCategory

    cat = db.query(BudgetCategory).filter(BudgetCategory.id == category_id).first()
    if cat is None or cat.wedding_id != wedding_id:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


def _get_expense_or_404(db: Session, wedding_id: int, expense_id: int):
    from app.models import Expense

    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if expense is None or expense.wedding_id != wedding_id:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


def _validate_vendor_in_wedding(db: Session, wedding_id: int, vendor_id: int):
    from app.models import Vendor

    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if vendor is None or vendor.wedding_id != wedding_id:
        raise HTTPException(status_code=404, detail="Vendor not found")


# ── Categories ────────────────────────────────────────────────────────────────


@router.get("/categories", response_model=list[BudgetCategoryPublic])
def list_categories(
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import BudgetCategory

    return (
        db.query(BudgetCategory)
        .filter(BudgetCategory.wedding_id == wedding.id)
        .order_by(BudgetCategory.id)
        .all()
    )


@router.post(
    "/categories", response_model=BudgetCategoryPublic, status_code=status.HTTP_201_CREATED
)
def create_category(
    body: BudgetCategoryCreate,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import BudgetCategory

    cat = BudgetCategory(wedding_id=wedding.id, **body.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.get("/categories/{category_id}", response_model=BudgetCategoryPublic)
def get_category(
    category_id: int,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    return _get_category_or_404(db, wedding.id, category_id)


@router.patch("/categories/{category_id}", response_model=BudgetCategoryPublic)
def patch_category(
    category_id: int,
    body: BudgetCategoryUpdate,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    cat = _get_category_or_404(db, wedding.id, category_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(cat, field, value)
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import Expense

    cat = _get_category_or_404(db, wedding.id, category_id)
    # Cascade delete expenses explicitly (ORM cascade also set, belt+suspenders)
    db.query(Expense).filter(Expense.category_id == cat.id).delete(synchronize_session=False)
    db.delete(cat)
    db.commit()


# ── Scale ─────────────────────────────────────────────────────────────────────


@router.post("/scale", response_model=ScaleBudgetResult)
def scale_budget(
    body: ScaleBudgetRequest,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    previous_total = wedding.total_budget or 0.0
    wedding.total_budget = body.new_total
    count = scale_categories(db, wedding.id, previous_total, body.new_total)
    db.commit()
    return ScaleBudgetResult(
        previous_total=previous_total,
        new_total=body.new_total,
        categories_scaled=count,
    )


# ── Expenses ──────────────────────────────────────────────────────────────────


@router.get("/expenses", response_model=list[ExpensePublic])
def list_expenses(
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import Expense

    return (
        db.query(Expense).filter(Expense.wedding_id == wedding.id).order_by(Expense.id.desc()).all()
    )


@router.post("/expenses", response_model=ExpensePublic, status_code=status.HTTP_201_CREATED)
def create_expense(
    body: ExpenseCreate,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import Expense

    _get_category_or_404(db, wedding.id, body.category_id)
    if body.vendor_id is not None:
        _validate_vendor_in_wedding(db, wedding.id, body.vendor_id)

    expense = Expense(wedding_id=wedding.id, **body.model_dump())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("/expenses/{expense_id}", response_model=ExpensePublic)
def get_expense(
    expense_id: int,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    return _get_expense_or_404(db, wedding.id, expense_id)


@router.patch("/expenses/{expense_id}", response_model=ExpensePublic)
def patch_expense(
    expense_id: int,
    body: ExpenseUpdate,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    expense = _get_expense_or_404(db, wedding.id, expense_id)
    update = body.model_dump(exclude_unset=True)

    if "category_id" in update and update["category_id"] is not None:
        _get_category_or_404(db, wedding.id, update["category_id"])
    if "vendor_id" in update and update["vendor_id"] is not None:
        _validate_vendor_in_wedding(db, wedding.id, update["vendor_id"])

    for field, value in update.items():
        setattr(expense, field, value)
    db.commit()
    db.refresh(expense)
    return expense


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    expense = _get_expense_or_404(db, wedding.id, expense_id)
    db.delete(expense)
    db.commit()


# ── Summary ───────────────────────────────────────────────────────────────────


@router.get("/summary", response_model=BudgetSummary)
def budget_summary(
    wedding: Annotated[object, Depends(require_wedding_access)],
    db: Annotated[Session, Depends(get_db)],
):
    from app.models import BudgetCategory, Expense

    spent_by_cat = dict(
        db.query(Expense.category_id, func.sum(Expense.actual_cost))
        .filter(Expense.actual_cost.isnot(None))
        .filter(Expense.wedding_id == wedding.id)
        .group_by(Expense.category_id)
        .all()
    )

    categories = (
        db.query(BudgetCategory)
        .filter(BudgetCategory.wedding_id == wedding.id)
        .order_by(BudgetCategory.id)
        .all()
    )

    summaries = []
    total_allocated = 0.0
    total_spent = 0.0

    for cat in categories:
        spent = float(spent_by_cat.get(cat.id, 0.0))
        allocated = float(cat.allocated_amount or 0.0)
        summaries.append(
            CategorySummary(
                category_id=cat.id,
                category_name=cat.name,
                allocated_amount=allocated,
                spent_amount=spent,
                remaining=allocated - spent,
            )
        )
        total_allocated += allocated
        total_spent += spent

    return BudgetSummary(
        total_allocated=total_allocated,
        total_spent=total_spent,
        total_remaining=total_allocated - total_spent,
        categories=summaries,
    )
