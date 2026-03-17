from flask import Blueprint, abort, flash, redirect, url_for, request
from flask_login import login_required, current_user

from app import db
from app.models import Guest, Wedding

guests_bp = Blueprint('guests', __name__)

_GUESTS_TAB = '#guests'

VALID_GROUPS = {'Bride\'s Family', 'Groom\'s Family', 'Friends', 'Colleagues', 'Other'}
VALID_MEALS  = {'Standard', 'Vegetarian', 'Vegan', 'Halal', 'Kosher', 'Other'}
VALID_RSVP   = {'pending', 'confirmed', 'declined'}


def _get_wedding_or_403(wedding_id):
    """Fetch wedding and abort 403 if it doesn't belong to the current user."""
    wedding = Wedding.query.get_or_404(wedding_id)
    if wedding.user_id != current_user.id:
        abort(403)
    return wedding


@guests_bp.route('/wedding/<int:wedding_id>/guests/add', methods=['POST'])
@login_required
def add_guest(wedding_id):
    _get_wedding_or_403(wedding_id)
    detail_url = url_for('wedding.wedding_detail', wedding_id=wedding_id) + _GUESTS_TAB

    full_name       = request.form.get('full_name',       '').strip()
    email           = request.form.get('email',           '').strip() or None
    phone           = request.form.get('phone',           '').strip() or None
    group_name      = request.form.get('group_name',      '').strip() or None
    meal_preference = request.form.get('meal_preference', '').strip() or None
    rsvp_status     = request.form.get('rsvp_status',     'pending').strip()

    if not full_name:
        flash('Guest name is required.', 'danger')
        return redirect(detail_url)

    if group_name and group_name not in VALID_GROUPS:
        flash('Invalid group selection.', 'danger')
        return redirect(detail_url)

    if meal_preference and meal_preference not in VALID_MEALS:
        flash('Invalid meal preference.', 'danger')
        return redirect(detail_url)

    if rsvp_status not in VALID_RSVP:
        rsvp_status = 'pending'

    guest = Guest(
        wedding_id=wedding_id,
        full_name=full_name,
        email=email,
        phone=phone,
        group_name=group_name,
        meal_preference=meal_preference,
        rsvp_status=rsvp_status,
    )
    db.session.add(guest)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Something went wrong adding the guest. Please try again.', 'danger')
        return redirect(detail_url)

    flash(f'{full_name} has been added to the guest list.', 'success')
    return redirect(detail_url)
