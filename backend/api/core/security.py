import bcrypt
from werkzeug.security import check_password_hash

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
