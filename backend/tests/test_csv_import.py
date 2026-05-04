import pytest

from api.core.csv_import import CSVImportError, parse_guest_csv
from api.schemas.guest import GuestCreate


def test_parse_minimal_csv():
    csv = b"full_name\nAlice\n"
    result = parse_guest_csv(csv, GuestCreate)
    assert len(result.rows) == 1
    assert result.rows[0]["full_name"] == "Alice"


def test_parse_strips_whitespace_in_values():
    csv = b"full_name,email\n  Alice  ,  alice@example.com  \n"
    result = parse_guest_csv(csv, GuestCreate)
    assert result.rows[0]["full_name"] == "Alice"
    assert result.rows[0]["email"] == "alice@example.com"


def test_parse_strips_whitespace_in_headers():
    csv = b"  full_name  ,  email  \nAlice,alice@example.com\n"
    result = parse_guest_csv(csv, GuestCreate)
    assert result.rows[0]["full_name"] == "Alice"


def test_parse_empty_optional_becomes_none():
    csv = b"full_name,email,phone\nAlice,,\n"
    result = parse_guest_csv(csv, GuestCreate)
    assert result.rows[0]["email"] is None
    assert result.rows[0]["phone"] is None


def test_parse_empty_rsvp_defaults_to_pending():
    csv = b"full_name,rsvp_status\nAlice,\n"
    result = parse_guest_csv(csv, GuestCreate)
    assert result.rows[0]["rsvp_status"] == "pending"


def test_parse_rejects_invalid_email():
    csv = b"full_name,email\nAlice,not-an-email\n"
    with pytest.raises(CSVImportError) as exc_info:
        parse_guest_csv(csv, GuestCreate)
    assert hasattr(exc_info.value, "row_errors")
    assert len(exc_info.value.row_errors) == 1
    assert exc_info.value.row_errors[0].row == 1
    assert "email" in exc_info.value.row_errors[0].errors


def test_parse_rejects_missing_required_column():
    csv = b"email,phone\nalice@example.com,+61400111222\n"
    with pytest.raises(CSVImportError) as exc_info:
        parse_guest_csv(csv, GuestCreate)
    assert "full_name" in str(exc_info.value)


def test_parse_rejects_oversized_file():
    big = b"full_name\n" + b"A" * (2 * 1024 * 1024)
    with pytest.raises(CSVImportError) as exc_info:
        parse_guest_csv(big, GuestCreate)
    assert "too large" in str(exc_info.value).lower()


def test_parse_handles_bom():
    csv = b"\xef\xbb\xbffull_name\nAlice\n"
    result = parse_guest_csv(csv, GuestCreate)
    assert result.rows[0]["full_name"] == "Alice"


def test_parse_rejects_invalid_utf8():
    csv = b"full_name\n\xff\xfe\xfd\n"
    with pytest.raises(CSVImportError) as exc_info:
        parse_guest_csv(csv, GuestCreate)
    assert "utf-8" in str(exc_info.value).lower()
