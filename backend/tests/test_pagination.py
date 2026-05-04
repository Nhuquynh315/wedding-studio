import base64
import json

import pytest

from api.core.pagination import InvalidCursorError, decode_cursor, encode_cursor


def test_cursor_round_trip():
    cursor = encode_cursor(42)
    assert decode_cursor(cursor) == 42


def test_cursor_round_trip_large_id():
    cursor = encode_cursor(9999999999)
    assert decode_cursor(cursor) == 9999999999


def test_decode_garbage_raises():
    with pytest.raises(InvalidCursorError):
        decode_cursor("not-base64!")
    with pytest.raises(InvalidCursorError):
        decode_cursor("")


def test_decode_valid_base64_but_not_json_raises():
    not_json = base64.urlsafe_b64encode(b"hello").decode("ascii")
    with pytest.raises(InvalidCursorError):
        decode_cursor(not_json)


def test_decode_json_missing_id_raises():
    payload = base64.urlsafe_b64encode(json.dumps({"foo": "bar"}).encode()).decode("ascii")
    with pytest.raises(InvalidCursorError):
        decode_cursor(payload)


def test_decode_json_id_not_int_raises():
    payload = base64.urlsafe_b64encode(json.dumps({"id": "abc"}).encode()).decode("ascii")
    with pytest.raises(InvalidCursorError):
        decode_cursor(payload)
