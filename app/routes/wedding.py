import re
from collections import defaultdict
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user

from app import db
from app.models import Wedding, WEDDING_STYLES
from app.routes.utils import get_wedding_or_403

_HEX_COLOR = re.compile(r'^#[0-9a-fA-F]{6}$')

wedding_bp = Blueprint('wedding', __name__)


@wedding_bp.route('/')
@wedding_bp.route('/dashboard')
def dashboard():
    weddings = []
    if current_user.is_authenticated:
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


@wedding_bp.route('/wedding/<int:wedding_id>')
@login_required
def wedding_detail(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    guests = wedding.guests
    total    = len(guests)
    accepted = sum(1 for g in guests if g.rsvp_status == 'confirmed')
    declined = sum(1 for g in guests if g.rsvp_status == 'declined')
    pending  = sum(1 for g in guests if g.rsvp_status == 'pending')
    responded = accepted + declined  # anyone who made a decision

    # Meal breakdown — count only guests with a non-null preference
    meal_counts = defaultdict(int)
    for g in guests:
        if g.meal_preference:
            meal_counts[g.meal_preference] += 1

    guest_stats = {
        'total':          total,
        'accepted':       accepted,
        'declined':       declined,
        'pending':        pending,
        'responded':      responded,
        'response_rate':  round(responded / total * 100) if total else 0,
        'dietary_count':  sum(1 for g in guests
                              if g.meal_preference and g.meal_preference != 'Standard'),
        'meal_counts':    dict(sorted(meal_counts.items())),
        'no_meal':        sum(1 for g in guests if not g.meal_preference),
    }

    # Per-group breakdown: { group_name: {total, accepted, pending, declined} }
    group_stats = defaultdict(lambda: {'total': 0, 'accepted': 0, 'pending': 0, 'declined': 0})
    for g in guests:
        key = g.group_name or 'Ungrouped'
        group_stats[key]['total'] += 1
        if g.rsvp_status == 'confirmed':
            group_stats[key]['accepted'] += 1
        elif g.rsvp_status == 'declined':
            group_stats[key]['declined'] += 1
        else:
            group_stats[key]['pending'] += 1
    group_stats = dict(sorted(group_stats.items()))

    return render_template('wedding/detail.html', wedding=wedding,
                           guest_stats=guest_stats, group_stats=group_stats)


@wedding_bp.route('/wedding/<int:wedding_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_wedding(wedding_id):
    wedding = get_wedding_or_403(wedding_id)

    if request.method == 'POST':
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
            return render_template('wedding/edit.html', wedding=wedding)

        wedding.partner1_name   = partner1_name
        wedding.partner2_name   = partner2_name
        wedding.wedding_date    = wedding_date
        wedding.location        = location
        wedding.venue_name      = venue_name
        wedding.style           = style
        wedding.primary_color   = primary_color
        wedding.secondary_color = secondary_color

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash('Something went wrong saving your changes. Please try again.', 'danger')
            return render_template('wedding/edit.html', wedding=wedding)

        flash('Wedding updated successfully.', 'success')
        return redirect(url_for('wedding.wedding_detail', wedding_id=wedding.id))

    return render_template('wedding/edit.html', wedding=wedding)


@wedding_bp.route('/wedding/<int:wedding_id>/delete', methods=['POST'])
@login_required
def delete_wedding(wedding_id):
    wedding = get_wedding_or_403(wedding_id)

    name = f"{wedding.partner1_name} & {wedding.partner2_name}"
    try:
        db.session.delete(wedding)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Something went wrong deleting the wedding. Please try again.', 'danger')
        return redirect(url_for('wedding.wedding_detail', wedding_id=wedding_id))

    flash(f"{name}'s wedding has been deleted.", 'success')
    return redirect(url_for('wedding.dashboard'))
