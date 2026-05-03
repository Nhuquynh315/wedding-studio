from datetime import UTC, datetime, timedelta
from typing import Literal

import bcrypt
from jose import JWTError, jwt
from werkzeug.security import check_password_hash

from api.core.config import settings
from api.schemas.auth import TokenPayload

# bcrypt hashes always start with one of these prefixes (per the
# bcrypt spec). Anything else is treated as a legacy werkzeug hash.
_BCRYPT_PREFIXES = ("$2b$", "$2a$", "$2y$")


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Note: bcrypt silently truncates passwords longer than 72 bytes.
    The schema enforces max_length=128 but only the first 72 bytes
    affect the hash. Acceptable trade-off for this app.
    """
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash.

    Recognizes both bcrypt (current) and werkzeug (legacy Flask) hashes.
    Returns False on any malformed input rather than crashing.
    """
    if not hashed_password:
        return False
    try:
        if hashed_password.startswith(_BCRYPT_PREFIXES):
            return bcrypt.checkpw(
                plain_password.encode("utf-8"),
                hashed_password.encode("utf-8"),
            )
        # Anything else: assume werkzeug-format (scrypt:, pbkdf2:, etc.)
        return check_password_hash(hashed_password, plain_password)
    except (ValueError, TypeError):
        return False


def needs_rehash(hashed_password: str) -> bool:
    """Returns True if this hash should be replaced with a fresh bcrypt
    hash on next successful login (e.g. legacy werkzeug hashes).

    Used by the login route to migrate existing Flask users to bcrypt
    transparently. Will be wired up in Prompt 6.
    """
    return not hashed_password.startswith(_BCRYPT_PREFIXES)


# ── JWT ───────────────────────────────────────────────────────────────────────


class InvalidTokenError(Exception):
    """Raised when a JWT cannot be decoded or is otherwise invalid."""


def _create_token(
    subject: str | int,
    token_type: Literal["access", "refresh"],
    expires_delta: timedelta,
) -> str:
    """Internal helper — encode a JWT with subject, type, and expiry."""
    expire = datetime.now(UTC) + expires_delta
    payload = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "type": token_type,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_access_token(subject: str | int) -> str:
    """Create a short-lived access token (default 15 min).

    The subject is typically a user ID. It will be coerced to str
    per JWT spec.
    """
    return _create_token(
        subject,
        "access",
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(subject: str | int) -> str:
    """Create a long-lived refresh token (default 7 days)."""
    return _create_token(
        subject,
        "refresh",
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT.

    Returns the TokenPayload on success. Raises InvalidTokenError
    on any failure: bad signature, expired token, malformed payload,
    wrong algorithm, missing fields, etc.
    """
    try:
        raw = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise InvalidTokenError(str(exc)) from exc

    try:
        return TokenPayload(**raw)
    except (TypeError, ValueError) as exc:
        raise InvalidTokenError(f"Invalid token payload: {exc}") from exc
