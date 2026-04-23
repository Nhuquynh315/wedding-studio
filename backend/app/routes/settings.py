import re
from datetime import datetime, timezone

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, logout_user

from app import db
from app.models import User

settings_bp = Blueprint('settings', __name__)

_EMAIL_RE  = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
_HEX_RE    = re.compile(r'^#[0-9a-fA-F]{6}$')

_TIMEZONES = [
    'UTC', 'US/Eastern', 'US/Central', 'US/Mountain', 'US/Pacific',
    'Europe/London', 'Europe/Paris', 'Asia/Tokyo', 'Asia/Singapore', 'Australia/Sydney',
]

_VALID_TIMEZONES = set(_TIMEZONES)


@settings_bp.route('/settings')
@login_required
def settings_page():
    return render_template('settings.html', timezones=_TIMEZONES)


@settings_bp.route('/settings/profile', methods=['POST'])
@login_required
def update_profile():
    full_name = request.form.get('full_name', '').strip()
    phone     = request.form.get('phone',     '').strip()
    tz        = request.form.get('timezone',  'UTC').strip()

    if not full_name:
        flash('Full name is required.', 'danger')
        return redirect(url_for('settings.settings_page'))
    if tz not in _VALID_TIMEZONES:
        tz = 'UTC'

    current_user.full_name  = full_name
    current_user.phone      = phone or None
    current_user.timezone   = tz
    current_user.updated_at = datetime.now(timezone.utc)

    try:
        db.session.commit()
        flash('Your profile has been updated.', 'success')
    except Exception:
        db.session.rollback()
        flash('Could not save profile. Please try again.', 'danger')

    return redirect(url_for('settings.settings_page'))


@settings_bp.route('/settings/email', methods=['POST'])
@login_required
def update_email():
    new_email = request.form.get('new_email', '').strip().lower()
    password  = request.form.get('password',  '')

    if not new_email or not _EMAIL_RE.match(new_email):
        flash('Please enter a valid email address.', 'danger')
        return redirect(url_for('settings.settings_page'))

    if not current_user.check_password(password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('settings.settings_page'))

    if User.query.filter_by(email=new_email).first():
        flash('An account with that email already exists.', 'danger')
        return redirect(url_for('settings.settings_page'))

    current_user.email      = new_email
    current_user.updated_at = datetime.now(timezone.utc)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Could not update email. Please try again.', 'danger')
        return redirect(url_for('settings.settings_page'))

    logout_user()
    session.clear()
    flash('Email updated. Please log in again.', 'success')
    return redirect(url_for('auth.login'))


@settings_bp.route('/settings/password', methods=['POST'])
@login_required
def update_password():
    current_pw = request.form.get('current_password', '')
    new_pw     = request.form.get('new_password',     '')
    confirm_pw = request.form.get('confirm_password', '')

    if not current_user.check_password(current_pw):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('settings.settings_page'))

    if new_pw != confirm_pw:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('settings.settings_page'))

    if len(new_pw) < 8:
        flash('New password must be at least 8 characters.', 'danger')
        return redirect(url_for('settings.settings_page'))

    current_user.set_password(new_pw)
    current_user.updated_at = datetime.now(timezone.utc)

    try:
        db.session.commit()
        flash('Password updated successfully.', 'success')
    except Exception:
        db.session.rollback()
        flash('Could not update password. Please try again.', 'danger')

    return redirect(url_for('settings.settings_page'))


@settings_bp.route('/settings/notifications', methods=['POST'])
@login_required
def update_notifications():
    if request.is_json:
        enabled = bool(request.json.get('enabled', True))
    else:
        enabled = request.form.get('enabled') == 'true'

    current_user.email_notifications = enabled
    current_user.updated_at          = datetime.now(timezone.utc)

    try:
        db.session.commit()
        return jsonify({'ok': True, 'enabled': enabled})
    except Exception:
        db.session.rollback()
        return jsonify({'ok': False, 'error': 'Could not save preference.'}), 500


@settings_bp.route('/settings/avatar-color', methods=['POST'])
@login_required
def update_avatar_color():
    if request.is_json:
        color = request.json.get('color', '').strip()
    else:
        color = request.form.get('color', '').strip()

    if not _HEX_RE.match(color):
        return jsonify({'ok': False, 'error': 'Invalid color value.'}), 400

    current_user.avatar_color = color
    current_user.updated_at   = datetime.now(timezone.utc)

    try:
        db.session.commit()
        return jsonify({'ok': True, 'color': color})
    except Exception:
        db.session.rollback()
        return jsonify({'ok': False, 'error': 'Could not save color.'}), 500


@settings_bp.route('/settings/delete-account', methods=['POST'])
@login_required
def delete_account():
    password     = request.form.get('password',     '')
    confirm_text = request.form.get('confirm_text', '')

    if confirm_text != 'DELETE':
        flash('Please type DELETE to confirm account deletion.', 'danger')
        return redirect(url_for('settings.settings_page'))

    if not current_user.check_password(password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('settings.settings_page'))

    user = current_user._get_current_object()
    try:
        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Could not delete account. Please try again.', 'danger')
        return redirect(url_for('settings.settings_page'))

    logout_user()
    session.clear()
    return redirect(url_for('wedding.dashboard'))
