from typing import Annotated

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from api.core.db import get_db
from api.core.security import InvalidTokenError, decode_token

# tokenUrl is the path Swagger UI's "Authorize" button POSTs to.
# We don't actually use OAuth2 password flow — this is just the
# standard pattern for "extract Bearer token from Authorization header".
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
):
    """Resolve the User row for a request's Bearer token.

    Raises 401 if:
    - Token is missing/malformed/expired/wrong-signature
    - Token type is not 'access' (refresh tokens can't authorize requests)
    - User ID in token doesn't exist in DB
    """
    from app.models import User  # delayed import — Flask-SQLAlchemy quirk

    try:
        payload = decode_token(token)
    except InvalidTokenError as exc:
        raise _credentials_exception from exc

    if payload.type != "access":
        raise _credentials_exception

    try:
        user_id = int(payload.sub)
    except ValueError as exc:
        raise _credentials_exception from exc

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise _credentials_exception

    return user


def require_wedding_access(
    wedding_id: Annotated[int, Path()],
    current_user: Annotated[object, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Resolve a Wedding for a given path parameter, enforcing ownership.

    Returns the Wedding row if it exists AND is owned by the current
    user. Raises 404 in either failure case (existence is hidden from
    unauthorized users by deliberate design).

    Usage:
        @router.get("/{wedding_id}/guests")
        def list_guests(wedding: Wedding = Depends(require_wedding_access)):
            ...
    """
    from app.models import Wedding

    wedding = db.query(Wedding).filter(Wedding.id == wedding_id).first()
    if wedding is None or wedding.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wedding not found",
        )
    return wedding
