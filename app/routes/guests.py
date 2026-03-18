from flask import Blueprint, abort, flash, redirect, url_for, request
from flask_login import login_required, current_user

from app import db
from app.models import Guest, Wedding
from app.services.csv_service import parse_guest_csv

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


def _get_guest_or_403(guest_id):
    """Fetch guest and abort 403 if its wedding doesn't belong to the current user."""
    guest = Guest.query.get_or_404(guest_id)
    if guest.wedding.user_id != current_user.id:
        abort(403)
    return guest


@guests_bp.route('/guest/<int:guest_id>/edit', methods=['POST'])
@login_required
def edit_guest(guest_id):
    guest = _get_guest_or_403(guest_id)
    detail_url = url_for('wedding.wedding_detail', wedding_id=guest.wedding_id) + _GUESTS_TAB

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

    guest.full_name       = full_name
    guest.email           = email
    guest.phone           = phone
    guest.group_name      = group_name
    guest.meal_preference = meal_preference
    guest.rsvp_status     = rsvp_status

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Something went wrong updating the guest. Please try again.', 'danger')
        return redirect(detail_url)

    flash(f'{full_name} has been updated.', 'success')
    return redirect(detail_url)


@guests_bp.route('/wedding/<int:wedding_id>/guests/import-csv', methods=['POST'])
@login_required
def import_guests(wedding_id):
    _get_wedding_or_403(wedding_id)
    detail_url = url_for('wedding.wedding_detail', wedding_id=wedding_id) + _GUESTS_TAB

    csv_file = request.files.get('csv_file')
    if not csv_file or csv_file.filename == '':
        flash('Please select a CSV file to upload.', 'danger')
        return redirect(detail_url)

    if not csv_file.filename.lower().endswith('.csv'):
        flash('Only .csv files are accepted.', 'danger')
        return redirect(detail_url)

    guests, errors = parse_guest_csv(csv_file)

    if not guests and errors:
        for msg in errors:
            flash(msg, 'danger')
        return redirect(detail_url)

    for data in guests:
        db.session.add(Guest(wedding_id=wedding_id, **data))

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Something went wrong saving the imported guests. Please try again.', 'danger')
        return redirect(detail_url)

    imported = len(guests)
    skipped  = len(errors)
    summary  = f'{imported} guest{"s" if imported != 1 else ""} imported'
    if skipped:
        summary += f', {skipped} row{"s" if skipped > 1 else ""} skipped'
    summary += '.'
    flash(summary, 'success' if not skipped else 'warning')

    for msg in errors:
        flash(msg, 'warning')

    return redirect(detail_url)


@guests_bp.route('/guest/<int:guest_id>/delete', methods=['POST'])
@login_required
def delete_guest(guest_id):
    guest = _get_guest_or_403(guest_id)
    detail_url = url_for('wedding.wedding_detail', wedding_id=guest.wedding_id) + _GUESTS_TAB

    name = guest.full_name
    try:
        db.session.delete(guest)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Something went wrong deleting the guest. Please try again.', 'danger')
        return redirect(detail_url)

    flash(f'{name} has been removed from the guest list.', 'success')
    return redirect(detail_url)
