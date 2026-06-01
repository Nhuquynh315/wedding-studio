from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from api.core.config import settings
from api.core.db import get_db
from api.core.deps import get_current_user
from api.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    is_token_revoked,
    needs_rehash,
    revoke_token,
    verify_password,
)
from api.schemas.auth import (
    PasswordChange,
    RefreshRequest,
    Token,
    UserCreate,
    UserLogin,
    UserPublic,
    UserUpdate,
)

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

    refresh_token, _ = create_refresh_token(subject=user.id)
    return Token(
        access_token=create_access_token(subject=user.id),
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=Token)
def refresh(
    body: RefreshRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Exchange a valid refresh token for new access + refresh tokens.

    The incoming refresh token is blocklisted after use — single-use rotation.
    Tokens issued before jti support (pre-8A) are rejected.
    """
    from app.models import User

    try:
        payload = jwt.decode(
            body.refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError as exc:
        raise _bad_token from exc

    if payload.get("type") != "refresh":
        raise _bad_token

    jti = payload.get("jti")
    if not jti:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing identifier; please log in again",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if is_token_revoked(db, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(payload["sub"])
    except (ValueError, KeyError) as exc:
        raise _bad_token from exc

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise _bad_token

    old_expires = datetime.fromtimestamp(payload["exp"], tz=UTC)
    revoke_token(db, jti=jti, user_id=user.id, expires_at=old_expires)

    new_refresh, _ = create_refresh_token(subject=user.id)
    return Token(
        access_token=create_access_token(subject=user.id),
        refresh_token=new_refresh,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    body: RefreshRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Blocklist the user's refresh token. Idempotent.

    Accepts any well-formed refresh token. Does not error on already-revoked
    or expired tokens — the desired post-state is 'token is revoked', which
    is already true in both cases. Does not require a Bearer auth header
    because the refresh token itself is the credential being surrendered.
    """
    try:
        payload = jwt.decode(
            body.refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        return Response(status_code=204)

    if payload.get("type") != "refresh":
        return Response(status_code=204)

    jti = payload.get("jti")
    if not jti:
        return Response(status_code=204)

    user_id = int(payload["sub"])
    expires_at = datetime.fromtimestamp(payload["exp"], tz=UTC)
    revoke_token(db, jti=jti, user_id=user_id, expires_at=expires_at)
    return Response(status_code=204)


@router.get("/me", response_model=UserPublic)
def me(current_user: Annotated[object, Depends(get_current_user)]):
    """Return the authenticated user's public info."""
    return current_user


@router.patch("/me", response_model=UserPublic)
def update_me(
    body: UserUpdate,
    current_user: Annotated[object, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Update the authenticated user's profile. PATCH semantics — only
    provided fields change."""
    from app.models import User

    updates = body.model_dump(exclude_unset=True)

    if "email" in updates and updates["email"] != current_user.email:
        existing = db.query(User).filter(User.email == updates["email"]).first()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="That email is already in use.",
            )

    for field, value in updates.items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: PasswordChange,
    current_user: Annotated[object, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Change the authenticated user's password. Requires the current
    password for verification.

    Note: does not rotate the JWT or invalidate other sessions. Token
    blocklist is deferred to Phase 5 hardening.
    """
    from fastapi.responses import Response as FastAPIResponse

    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    current_user.password_hash = hash_password(body.new_password)
    db.commit()
    return FastAPIResponse(status_code=status.HTTP_204_NO_CONTENT)
