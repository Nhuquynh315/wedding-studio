from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.core.db import get_db
from api.core.deps import get_current_user
from api.core.security import (
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    needs_rehash,
    verify_password,
)
from api.schemas.auth import Token, UserCreate, UserLogin, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])

_bad_credentials = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect email or password",
)

_bad_token = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired token",
    headers={"WWW-Authenticate": "Bearer"},
)


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_in: UserCreate,
    db: Annotated[Session, Depends(get_db)],
):
    """Register a new user. Returns the public user record (no token).

    Client should call /login next to get tokens.
    """
    from app.models import User

    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        password_hash=hash_password(user_in.password),
        created_at=datetime.now(UTC),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    creds: UserLogin,
    db: Annotated[Session, Depends(get_db)],
):
    """Verify credentials, return access + refresh tokens.

    Transparently rehashes legacy (werkzeug) password hashes to bcrypt
    on successful login.
    """
    from app.models import User

    user = db.query(User).filter(User.email == creds.email).first()

    if user is None or not verify_password(creds.password, user.password_hash):
        raise _bad_credentials

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(creds.password)
        db.commit()

    return Token(
        access_token=create_access_token(subject=user.id),
        refresh_token=create_refresh_token(subject=user.id),
    )


@router.post("/refresh", response_model=Token)
def refresh(
    refresh_token: Annotated[str, Body(..., embed=True)],
    db: Annotated[Session, Depends(get_db)],
):
    """Exchange a valid refresh token for new access + refresh tokens."""
    from app.models import User

    try:
        payload = decode_token(refresh_token)
    except InvalidTokenError as exc:
        raise _bad_token from exc

    if payload.type != "refresh":
        raise _bad_token

    try:
        user_id = int(payload.sub)
    except ValueError as exc:
        raise _bad_token from exc

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise _bad_token

    return Token(
        access_token=create_access_token(subject=user.id),
        refresh_token=create_refresh_token(subject=user.id),
    )


@router.get("/me", response_model=UserPublic)
def me(current_user: Annotated[object, Depends(get_current_user)]):
    """Return the authenticated user's public info."""
    return current_user
