from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RSVPStatus(StrEnum):
    pending = "pending"
    confirmed = "confirmed"
    declined = "declined"


class GuestCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    group_name: str | None = Field(default=None, max_length=100)
    meal_preference: str | None = Field(default=None, max_length=100)
    rsvp_status: RSVPStatus = RSVPStatus.pending
    table_number: int | None = None
    table_id: int | None = None


class GuestUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    group_name: str | None = Field(default=None, max_length=100)
    meal_preference: str | None = Field(default=None, max_length=100)
    rsvp_status: RSVPStatus | None = None
    table_number: int | None = None
    table_id: int | None = None


class GuestPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    wedding_id: int
    full_name: str
    email: str | None = None
    phone: str | None = None
    group_name: str | None = None
    meal_preference: str | None = None
    rsvp_status: RSVPStatus
    table_number: int | None = None
    table_id: int | None = None
    created_at: datetime
