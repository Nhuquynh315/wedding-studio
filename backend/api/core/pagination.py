import base64
import json

from fastapi import HTTPException, status


class InvalidCursorError(Exception):
    """Raised when a cursor cannot be decoded."""


def encode_cursor(last_id: int) -> str:
    """Encode a last-seen ID into an opaque base64 cursor string."""
    payload = json.dumps({"id": last_id}, separators=(",", ":"))
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")


def decode_cursor(cursor: str) -> int:
    """Decode a cursor back to the last-seen ID.

    Raises InvalidCursorError on malformed input.
    """
    try:
        padding_needed = 4 - (len(cursor) % 4)
        if padding_needed != 4:
            cursor = cursor + ("=" * padding_needed)
        decoded = base64.urlsafe_b64decode(cursor.encode("ascii"))
        payload = json.loads(decoded.decode("utf-8"))
        if not isinstance(payload, dict) or "id" not in payload:
            raise InvalidCursorError("missing 'id' in cursor")
        if not isinstance(payload["id"], int):
            raise InvalidCursorError("'id' must be an integer")
        return payload["id"]
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidCursorError(f"malformed cursor: {exc}") from exc


def cursor_or_422(cursor: str | None) -> int | None:
    """Decode an Optional[cursor] or raise 422."""
    if cursor is None:
        return None
    try:
        return decode_cursor(cursor)
    except InvalidCursorError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid cursor: {exc}",
        ) from exc
