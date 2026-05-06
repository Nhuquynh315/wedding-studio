from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

# ── Budget Category ───────────────────────────────────────────────────────────


class BudgetCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    allocated_amount: float = Field(ge=0)
    color: str | None = Field(default=None, max_length=7)


class BudgetCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    allocated_amount: float | None = Field(default=None, ge=0)
    color: str | None = Field(default=None, max_length=7)


class BudgetCategoryPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    wedding_id: int
    name: str
    allocated_amount: float
    color: str | None = None
    created_at: datetime


# ── Expense ───────────────────────────────────────────────────────────────────


class ExpenseCreate(BaseModel):
    category_id: int
    vendor_id: int | None = None
    title: str = Field(min_length=1, max_length=200)
    estimated_cost: float = Field(ge=0, default=0.0)
    actual_cost: float | None = Field(default=None, ge=0)
    is_paid: bool = False
    paid_date: date | None = None
    due_date: date | None = None
    notes: str | None = None


class ExpenseUpdate(BaseModel):
    category_id: int | None = None
    vendor_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    estimated_cost: float | None = Field(default=None, ge=0)
    actual_cost: float | None = Field(default=None, ge=0)
    is_paid: bool | None = None
    paid_date: date | None = None
    due_date: date | None = None
    notes: str | None = None


class ExpensePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    wedding_id: int
    category_id: int | None = None
    vendor_id: int | None = None
    title: str
    estimated_cost: float
    actual_cost: float | None = None
    is_paid: bool
    paid_date: date | None = None
    due_date: date | None = None
    notes: str | None = None
    created_at: datetime


# ── Scaling endpoint ──────────────────────────────────────────────────────────


class ScaleBudgetRequest(BaseModel):
    new_total: float = Field(gt=0)


class ScaleBudgetResult(BaseModel):
    previous_total: float
    new_total: float
    categories_scaled: int


# ── Summary endpoint ──────────────────────────────────────────────────────────


class CategorySummary(BaseModel):
    category_id: int
    category_name: str
    allocated_amount: float
    spent_amount: float
    remaining: float


class BudgetSummary(BaseModel):
    total_allocated: float
    total_spent: float
    total_remaining: float
    categories: list[CategorySummary]
