import csv
import io
from dataclasses import dataclass

from pydantic import ValidationError

_MAX_FILE_SIZE_BYTES = 1024 * 1024  # 1 MB
_RECOGNIZED_COLUMNS = {
    "full_name",
    "email",
    "phone",
    "group_name",
    "meal_preference",
    "rsvp_status",
}
_REQUIRED_COLUMNS = {"full_name"}


class CSVImportError(Exception):
    """Top-level errors that prevent any rows from being parsed."""


@dataclass
class RowError:
    """One row failed validation."""

    row: int  # 1-indexed, NOT including the header row
    errors: dict  # field name → list of error messages


@dataclass
class CSVParseResult:
    """Successful parse: rows is a list of validated dicts ready for INSERT."""

    rows: list[dict]


def parse_guest_csv(
    file_bytes: bytes,
    schema_class,  # the Pydantic class to validate each row against (GuestCreate)
) -> CSVParseResult:
    """Parse and validate a CSV file as guest data.

    Returns CSVParseResult on success.
    Raises CSVImportError if the file is malformed at the top level
    (size, encoding, missing required column).
    Raises CSVImportError with row_errors attribute if any row fails validation.
    """
    if len(file_bytes) > _MAX_FILE_SIZE_BYTES:
        raise CSVImportError(
            f"File too large: {len(file_bytes)} bytes (max {_MAX_FILE_SIZE_BYTES})"
        )

    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise CSVImportError(f"File must be UTF-8 encoded: {exc}") from exc

    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        raise CSVImportError("CSV file is empty")

    reader.fieldnames = [name.strip() for name in reader.fieldnames]

    missing = _REQUIRED_COLUMNS - set(reader.fieldnames)
    if missing:
        raise CSVImportError(f"Missing required column(s): {', '.join(sorted(missing))}")

    validated_rows: list[dict] = []
    row_errors: list[RowError] = []

    for idx, raw_row in enumerate(reader, start=1):
        cleaned = {}
        for key, value in raw_row.items():
            if key not in _RECOGNIZED_COLUMNS:
                continue
            stripped = (value or "").strip()
            if stripped == "":
                if key == "rsvp_status":
                    stripped = "pending"
                else:
                    cleaned[key] = None
                    continue
            cleaned[key] = stripped

        try:
            validated = schema_class(**cleaned)
        except ValidationError as exc:
            row_errors.append(RowError(row=idx, errors=_format_validation_errors(exc)))
            continue

        data = validated.model_dump()
        if "rsvp_status" in data and hasattr(data["rsvp_status"], "value"):
            data["rsvp_status"] = data["rsvp_status"].value
        validated_rows.append(data)

    if row_errors:
        err = CSVImportError(f"{len(row_errors)} row(s) failed validation")
        err.row_errors = row_errors  # type: ignore[attr-defined]
        raise err

    return CSVParseResult(rows=validated_rows)


def _format_validation_errors(exc: ValidationError) -> dict:
    """Format Pydantic ValidationError into {field: [msg, ...]}."""
    result: dict[str, list[str]] = {}
    for err in exc.errors():
        field = ".".join(str(p) for p in err["loc"]) if err["loc"] else "_root"
        result.setdefault(field, []).append(err["msg"])
    return result
