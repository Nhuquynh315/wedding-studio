from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from api.core.config import settings
from api.core.security import (
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_access_token_round_trip():
    """Create an access token, decode it, get back the same subject."""
    token = create_access_token(subject=42)
    payload = decode_token(token)

    assert payload.sub == "42"  # always coerced to str
    assert payload.type == "access"
    expected_exp = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    assert abs(payload.exp - int(expected_exp.timestamp())) < 5


def test_refresh_token_round_trip():
    """Refresh tokens should encode type='refresh' with a longer expiry."""
    token = create_refresh_token(subject="user-99")
    payload = decode_token(token)

    assert payload.sub == "user-99"
    assert payload.type == "refresh"
    expected_exp = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    assert abs(payload.exp - int(expected_exp.timestamp())) < 5


def test_string_and_int_subjects_both_work():
    """Subject can be int or str; both are stored as str."""
    int_token = create_access_token(subject=1)
    str_token = create_access_token(subject="1")

    assert decode_token(int_token).sub == "1"
    assert decode_token(str_token).sub == "1"


def test_decode_rejects_garbage_token():
    with pytest.raises(InvalidTokenError):
        decode_token("not.a.token")
    with pytest.raises(InvalidTokenError):
        decode_token("")
    with pytest.raises(InvalidTokenError):
        decode_token("a.b.c")


def test_decode_rejects_token_signed_with_wrong_secret():
    """A token signed with a different secret must be rejected."""
    fake_token = jwt.encode(
        {"sub": "1", "exp": int(datetime.now(UTC).timestamp()) + 60, "type": "access"},
        "completely-different-secret",
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidTokenError):
        decode_token(fake_token)


def test_decode_rejects_expired_token():
    """An expired token must be rejected even if signature is valid."""
    expired_token = jwt.encode(
        {
            "sub": "1",
            "exp": int((datetime.now(UTC) - timedelta(minutes=1)).timestamp()),
            "type": "access",
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidTokenError):
        decode_token(expired_token)


def test_decode_rejects_payload_missing_required_fields():
    """A token with no 'type' field should fail TokenPayload validation."""
    incomplete = jwt.encode(
        {"sub": "1", "exp": int(datetime.now(UTC).timestamp()) + 60},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidTokenError):
        decode_token(incomplete)
