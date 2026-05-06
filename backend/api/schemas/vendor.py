from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class VendorStatus(StrEnum):
    considering = "considering"
    booked = "booked"
    rejected = "rejected"
    backup = "backup"


class VendorCreate(BaseModel):
    business_name: str = Field(min_length=1, max_length=200)
    category: str = Field(default="Other", max_length=50)
    contact_name: str | None = Field(default=None, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    website: str | None = Field(default=None, max_length=300)
    quoted_price: float | None = Field(default=None, ge=0)
    deposit_amount: float | None = Field(default=None, ge=0)
    deposit_paid: bool = False
    deposit_due_date: date | None = None
    contracted: bool = False
    contract_signed_date: date | None = None
    contract_url: str | None = Field(default=None, max_length=500)
    rating: int | None = Field(default=None, ge=0, le=5)
    notes: str | None = None
    status: VendorStatus = VendorStatus.considering
    final_payment_amount: float | None = Field(default=None, ge=0)
    final_payment_paid: bool = False
    final_payment_due_date: date | None = None


class VendorUpdate(BaseModel):
    business_name: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, max_length=50)
    contact_name: str | None = Field(default=None, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    website: str | None = Field(default=None, max_length=300)
    quoted_price: float | None = Field(default=None, ge=0)
    deposit_amount: float | None = Field(default=None, ge=0)
    deposit_paid: bool | None = None
    deposit_due_date: date | None = None
    contracted: bool | None = None
    contract_signed_date: date | None = None
    contract_url: str | None = Field(default=None, max_length=500)
    rating: int | None = Field(default=None, ge=0, le=5)
    notes: str | None = None
    status: VendorStatus | None = None
    final_payment_amount: float | None = Field(default=None, ge=0)
    final_payment_paid: bool | None = None
    final_payment_due_date: date | None = None


class VendorPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    wedding_id: int
    business_name: str
    category: str
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    website: str | None = None
    quoted_price: float | None = None
    deposit_amount: float | None = None
    deposit_paid: bool
    deposit_due_date: date | None = None
    contracted: bool
    contract_signed_date: date | None = None
    contract_url: str | None = None
    rating: int | None = None
    notes: str | None = None
    status: VendorStatus
    final_payment_amount: float | None = None
    final_payment_paid: bool
    final_payment_due_date: date | None = None
    created_at: datetime
