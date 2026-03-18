from flask import abort
from flask_login import current_user

from app.models import Guest, Wedding


def get_wedding_or_403(wedding_id):
    """Fetch a wedding by ID and abort 403 if it doesn't belong to the current user."""
    wedding = Wedding.query.get_or_404(wedding_id)
    if wedding.user_id != current_user.id:
        abort(403)
    return wedding


def get_guest_or_403(guest_id):
    """Fetch a guest by ID and abort 403 if its wedding doesn't belong to the current user."""
    guest = Guest.query.get_or_404(guest_id)
    if guest.wedding_id is None or guest.wedding.user_id != current_user.id:
        abort(403)
    return guest
