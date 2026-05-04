from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class WeddingCreate(BaseModel):
    """Input for POST /api/v1/weddings."""

    partner1_name: str = Field(min_length=1, max_length=120)
    partner2_name: str = Field(min_length=1, max_length=120)
    wedding_date: date
    location: str = Field(min_length=1, max_length=255)
    venue_name: str = Field(min_length=1, max_length=255)
    style: str = Field(min_length=1, max_length=20)
    primary_color: str = Field(min_length=1, max_length=20)
    secondary_color: str = Field(min_length=1, max_length=20)
    rsvp_contact: str | None = Field(default=None, max_length=255)
    total_budget: float | None = Field(default=None, ge=0)


class WeddingUpdate(BaseModel):
    """Input for PATCH /api/v1/weddings/{wedding_id}.

    All fields optional — only provided fields will be updated.
    """

    partner1_name: str | None = Field(default=None, min_length=1, max_length=120)
    partner2_name: str | None = Field(default=None, min_length=1, max_length=120)
    wedding_date: date | None = None
    location: str | None = Field(default=None, min_length=1, max_length=255)
    venue_name: str | None = Field(default=None, min_length=1, max_length=255)
    style: str | None = Field(default=None, min_length=1, max_length=20)
    primary_color: str | None = Field(default=None, min_length=1, max_length=20)
    secondary_color: str | None = Field(default=None, min_length=1, max_length=20)
    rsvp_contact: str | None = Field(default=None, max_length=255)
    total_budget: float | None = Field(default=None, ge=0)


class WeddingPublic(BaseModel):
    """Wedding data returned in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    partner1_name: str
    partner2_name: str
    wedding_date: date
    location: str
    venue_name: str
    style: str
    primary_color: str
    secondary_color: str
    ai_generated_theme: str | None = None
    rsvp_contact: str | None = None
    total_budget: float | None = None
    created_at: datetime
    updated_at: datetime
