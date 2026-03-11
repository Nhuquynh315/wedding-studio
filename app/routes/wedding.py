import re
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user

from app import db
from app.models import Wedding, WEDDING_STYLES

_HEX_COLOR = re.compile(r'^#[0-9a-fA-F]{6}$')

wedding_bp = Blueprint('wedding', __name__)


@wedding_bp.route('/dashboard')
@login_required
def dashboard():
    weddings = Wedding.query.filter_by(user_id=current_user.id).order_by(Wedding.created_at.desc()).all()
    return render_template('dashboard.html', weddings=weddings)


@wedding_bp.route('/wedding/new', methods=['GET', 'POST'])
@login_required
def create_wedding():
    if request.method == 'POST':
        # Collect and validate required fields
        partner1_name   = request.form.get('partner1_name',   '').strip()
        partner2_name   = request.form.get('partner2_name',   '').strip()
        wedding_date_s  = request.form.get('wedding_date',    '').strip()
        location        = request.form.get('location',        '').strip()
        venue_name      = request.form.get('venue_name',      '').strip()
        style           = request.form.get('style',           '').strip()
        primary_color   = request.form.get('primary_color',   '').strip()
        secondary_color = request.form.get('secondary_color', '').strip()

        errors = []
        if not partner1_name:
            errors.append('Partner 1 name is required.')
        if not partner2_name:
            errors.append('Partner 2 name is required.')
        if not wedding_date_s:
            errors.append('Wedding date is required.')
        if not location:
            errors.append('Location is required.')
        if not venue_name:
            errors.append('Venue name is required.')
        if style not in WEDDING_STYLES:
            errors.append('Please select a valid wedding style.')
        if not _HEX_COLOR.match(primary_color):
            errors.append('Primary color must be a valid hex color (e.g. #ff5733).')
        if not _HEX_COLOR.match(secondary_color):
            errors.append('Secondary color must be a valid hex color (e.g. #ff5733).')

        wedding_date = None
        if wedding_date_s and not errors:
            try:
                wedding_date = date.fromisoformat(wedding_date_s)
            except ValueError:
                errors.append('Invalid wedding date format.')

        if errors:
            for msg in errors:
                flash(msg, 'danger')
            return render_template('wedding/create.html')

        wedding = Wedding(
            user_id=current_user.id,
            partner1_name=partner1_name,
            partner2_name=partner2_name,
            wedding_date=wedding_date,
            location=location,
            venue_name=venue_name,
            style=style,
            primary_color=primary_color,
            secondary_color=secondary_color,
        )
        db.session.add(wedding)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Something went wrong saving your wedding. Please try again.', 'danger')
            return render_template('wedding/create.html')

        flash(f"{partner1_name} & {partner2_name}'s wedding has been created!", 'success')
        return redirect(url_for('wedding.dashboard'))

    return render_template('wedding/create.html')
