from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Input for POST /api/v1/auth/register."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=200)


class UserLogin(BaseModel):
    """Input for POST /api/v1/auth/login."""

    email: EmailStr
    password: str


class UserPublic(BaseModel):
    """User data returned in API responses. Never includes password."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    created_at: datetime


class Token(BaseModel):
    """Response from /login and /refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT payload — used internally."""

    sub: str  # user id as string (JWT spec)
    exp: int  # unix timestamp
    type: str  # "access" or "refresh"
