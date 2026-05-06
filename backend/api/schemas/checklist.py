from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ChecklistCategory(StrEnum):
    venue = "Venue"
    catering = "Catering"
    attire = "Attire"
    photography = "Photography"
    flowers = "Flowers"
    music = "Music"
    stationery = "Stationery"
    transport = "Transport"
    honeymoon = "Honeymoon"
    other = "Other"


class ChecklistPriority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class ChecklistItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    category: ChecklistCategory = ChecklistCategory.other
    priority: ChecklistPriority = ChecklistPriority.medium
    due_date: date | None = None
    notes: str | None = None
    is_completed: bool = False


class ChecklistItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    category: ChecklistCategory | None = None
    priority: ChecklistPriority | None = None
    due_date: date | None = None
    notes: str | None = None
    is_completed: bool | None = None


class ChecklistItemPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    wedding_id: int
    title: str
    category: ChecklistCategory
    priority: ChecklistPriority
    due_date: date | None = None
    notes: str | None = None
    is_completed: bool
    completed_at: datetime | None = None
    created_at: datetime


# ── Bulk-complete ──────────────────────────────────────────────────────────────


class BulkCompleteRequest(BaseModel):
    completed: bool
    category: ChecklistCategory | None = None


class BulkCompleteResult(BaseModel):
    updated_count: int
