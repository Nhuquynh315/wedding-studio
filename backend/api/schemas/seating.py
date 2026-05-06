from pydantic import BaseModel, ConfigDict, Field

from api.schemas.guest import GuestPublic


class WeddingTableCreate(BaseModel):
    table_number: int = Field(ge=1)
    table_name: str | None = Field(default=None, min_length=1, max_length=100)
    capacity: int = Field(default=8, ge=1, le=100)
    shape: str = Field(default="round", max_length=20)
    position_x: float | None = None
    position_y: float | None = None
    notes: str | None = None


class WeddingTableUpdate(BaseModel):
    table_number: int | None = Field(default=None, ge=1)
    table_name: str | None = Field(default=None, min_length=1, max_length=100)
    capacity: int | None = Field(default=None, ge=1, le=100)
    shape: str | None = Field(default=None, max_length=20)
    position_x: float | None = None
    position_y: float | None = None
    notes: str | None = None


class WeddingTablePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    wedding_id: int
    table_number: int
    table_name: str | None = None
    capacity: int
    shape: str
    position_x: float | None = None
    position_y: float | None = None
    notes: str | None = None


class WeddingTableWithGuests(WeddingTablePublic):
    """Table with its assigned guests embedded — for the seating UI."""

    guests: list[GuestPublic] = []
