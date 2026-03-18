import csv
import io

VALID_GROUPS = {'Bride\'s Family', 'Groom\'s Family', 'Friends', 'Colleagues', 'Other'}
VALID_MEALS  = {'Standard', 'Vegetarian', 'Vegan', 'Halal', 'Kosher', 'Other'}
VALID_RSVP   = {'pending', 'confirmed', 'declined'}

EXPECTED_COLUMNS = {'full_name'}


def parse_guest_csv(file_obj):
    """
    Parse a CSV file of guests.

    Args:
        file_obj: A file-like object (binary or text) from request.files.

    Returns:
        (guests, errors) where:
          - guests is a list of dicts ready to pass to the Guest model
          - errors is a list of human-readable strings for skipped rows
    """
    guests = []
    errors = []

    # Wrap the binary stream in a text decoder.
    # Flask's FileStorage exposes the raw binary stream via .stream;
    # io.TextIOWrapper converts it to text without reading the whole file
    # into memory first. utf-8-sig also strips Excel's BOM if present.
    try:
        binary_stream = getattr(file_obj, 'stream', file_obj)
        try:
            text_stream = io.TextIOWrapper(binary_stream, encoding='utf-8-sig')
            # Force a small read to detect encoding errors early
            text_stream.read(0)
        except (UnicodeDecodeError, LookupError):
            binary_stream.seek(0)
            text_stream = io.TextIOWrapper(binary_stream, encoding='latin-1')
    except Exception as e:
        return [], [f'Could not read file: {e}']

    reader = csv.DictReader(text_stream)

    # Check that the required column exists
    if reader.fieldnames is None:
        return [], ['The file appears to be empty.']

    # Normalise header names (strip whitespace)
    normalised_headers = {h.strip() for h in reader.fieldnames if h}
    if 'full_name' not in normalised_headers:
        return [], ['Missing required column "full_name". Please check your CSV headers.']

    for line_num, row in enumerate(reader, start=2):  # start=2: row 1 is the header
        # Strip whitespace from all values
        row = {k.strip(): (v.strip() if v else '') for k, v in row.items() if k}

        full_name = row.get('full_name', '')
        if not full_name:
            errors.append(f'Row {line_num}: skipped — full_name is empty.')
            continue

        # Optional fields — None when blank so the model stores NULL
        email           = row.get('email')           or None
        phone           = row.get('phone')           or None
        group_name      = row.get('group_name')      or None
        meal_preference = row.get('meal_preference') or None
        rsvp_status     = row.get('rsvp_status', '').lower() or 'pending'

        # Validate controlled vocabularies and warn instead of hard-failing
        if group_name and group_name not in VALID_GROUPS:
            errors.append(
                f'Row {line_num} ({full_name}): unknown group "{group_name}" — set to blank.'
            )
            group_name = None

        if meal_preference and meal_preference not in VALID_MEALS:
            errors.append(
                f'Row {line_num} ({full_name}): unknown meal "{meal_preference}" — set to blank.'
            )
            meal_preference = None

        if rsvp_status not in VALID_RSVP:
            errors.append(
                f'Row {line_num} ({full_name}): unknown RSVP status "{rsvp_status}" — defaulted to "pending".'
            )
            rsvp_status = 'pending'

        guests.append({
            'full_name':       full_name,
            'email':           email,
            'phone':           phone,
            'group_name':      group_name,
            'meal_preference': meal_preference,
            'rsvp_status':     rsvp_status,
        })

    return guests, errors
