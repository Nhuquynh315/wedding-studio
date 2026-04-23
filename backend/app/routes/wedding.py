import contextlib
import json
import re
from collections import defaultdict
from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, send_file, session, url_for
from flask_login import current_user, login_required

from app import db
from app.models import WEDDING_STYLES, Guest, Wedding
from app.routes.utils import get_wedding_or_403
from app.services.ai_service import generate_wedding_theme
from app.services.pdf_service import generate_invitation_pdf

_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")

wedding_bp = Blueprint("wedding", __name__)


@wedding_bp.route("/")
@wedding_bp.route("/dashboard")
def dashboard():
    if not current_user.is_authenticated:
        return render_template("dashboard.html", active_wedding=None)

    weddings = Wedding.query.filter_by(user_id=current_user.id).order_by(Wedding.wedding_date).all()

    # Determine active wedding
    active_id = session.get("active_wedding_id")
    active = next((w for w in weddings if w.id == active_id), None) or (
        weddings[0] if weddings else None
    )
    if active:
        session["active_wedding_id"] = active.id

    if not active:
        return render_template("dashboard.html", active_wedding=None, weddings=weddings)

    # Guest stats for active wedding
    guests = active.guests
    total = len(guests)
    accepted = sum(1 for g in guests if g.rsvp_status == "confirmed")
    declined = sum(1 for g in guests if g.rsvp_status == "declined")
    pending = sum(1 for g in guests if g.rsvp_status == "pending")

    guest_stats = {
        "total": total,
        "accepted": accepted,
        "declined": declined,
        "pending": pending,
        "response_rate": round(accepted / total * 100) if total else 0,
    }

    # Checklist — use real DB items if they exist, else fallback to setup prompts
    from app.models import ChecklistItem

    cl_items = ChecklistItem.query.filter_by(wedding_id=active.id).all()
    today = date.today()
    if cl_items:
        cl_total = len(cl_items)
        cl_done = sum(1 for i in cl_items if i.is_completed)
        checklist_pct = round(cl_done / cl_total * 100) if cl_total else 0
        total_tasks = cl_total
        completed_count = cl_done
        has_any_tasks = True

        # Overdue count across all pending items (not capped)
        overdue_count = sum(
            1 for i in cl_items if not i.is_completed and i.due_date and i.due_date < today
        )

        # Pending tasks: sorted overdue-first then by due_date asc, no-date last. Limit 6.
        pending_tasks = sorted(
            [i for i in cl_items if not i.is_completed],
            key=lambda x: (x.due_date is None, x.due_date or date.max),
        )[:6]

        # Completed tasks: most recently completed first. Limit 3 (used as filler).
        completed_tasks = sorted(
            [i for i in cl_items if i.is_completed],
            key=lambda x: x.completed_at or datetime.min,
            reverse=True,
        )[:3]
    else:
        cl_total = 0
        cl_done = 0
        checklist_pct = 0
        total_tasks = 0
        completed_count = 0
        has_any_tasks = False
        overdue_count = 0
        pending_tasks = []
        completed_tasks = []

    days_until = (active.wedding_date - today).days if active.wedding_date else None

    # Budget stats for active wedding
    total_budget_amount = active.total_budget or 0
    cats = active.budget_categories
    total_actual_paid = sum(e.actual_cost or 0 for e in active.expenses if e.is_paid)
    budget_pct = round(total_actual_paid / total_budget_amount * 100) if total_budget_amount else 0
    # Top 3 categories by estimated spend for the snapshot card
    budget_snapshot = sorted(
        [
            {
                "name": c.name,
                "color": c.color,
                "allocated": c.allocated_amount,
                "estimated": sum(e.estimated_cost or 0 for e in c.expenses),
                "actual": sum(e.actual_cost or 0 for e in c.expenses if e.is_paid),
            }
            for c in cats
            if c.allocated_amount
        ],
        key=lambda x: x["estimated"],
        reverse=True,
    )[:3]

    # Next 3 vendor deposits not yet paid, sorted by due date
    upcoming_deposits = sorted(
        [
            v
            for v in active.vendors
            if v.deposit_due_date and not v.deposit_paid and v.deposit_due_date >= today
        ],
        key=lambda v: v.deposit_due_date,
    )[:3]

    # Recent activity: last 5 guests added across all weddings
    all_guests = []
    for w in weddings:
        all_guests.extend(w.guests)
    recent_guests = sorted(all_guests, key=lambda g: g.created_at, reverse=True)[:5]

    # Connection 3: cross-reference overdue tasks with vendor booking status
    from app.models import Vendor as VendorModel
    from app.utils.connections import VENDOR_TO_TASK

    warnings = []
    if has_any_tasks:
        overdue_items = ChecklistItem.query.filter(
            ChecklistItem.wedding_id == active.id,
            not ChecklistItem.is_completed,
            ChecklistItem.due_date < today,
        ).all()
        for item in overdue_items:
            title_lower = item.title.lower()
            for category, keywords in VENDOR_TO_TASK.items():
                if any(kw in title_lower for kw in keywords):
                    unbooked = (
                        VendorModel.query.filter_by(
                            wedding_id=active.id,
                            category=category,
                        )
                        .filter(VendorModel.status.in_(["considering", "backup"]))
                        .first()
                    )
                    if unbooked:
                        warnings.append(
                            {
                                "task": item.title,
                                "vendor_category": category,
                                "vendor_name": unbooked.business_name,
                                "days_overdue": (today - item.due_date).days,
                            }
                        )
                    elif not VendorModel.query.filter_by(
                        wedding_id=active.id,
                        category=category,
                    ).first():
                        warnings.append(
                            {
                                "task": item.title,
                                "vendor_category": category,
                                "vendor_name": None,
                                "days_overdue": (today - item.due_date).days,
                            }
                        )
                    break  # only match first keyword set per task

    return render_template(
        "dashboard.html",
        active_wedding=active,
        weddings=weddings,
        guest_stats=guest_stats,
        checklist_pct=checklist_pct,
        cl_done=cl_done,
        cl_total=cl_total,
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
        overdue_count=overdue_count,
        total_tasks=total_tasks,
        completed_count=completed_count,
        has_any_tasks=has_any_tasks,
        days_until=days_until,
        recent_guests=recent_guests,
        total_budget_amount=total_budget_amount,
        total_actual_paid=total_actual_paid,
        budget_pct=budget_pct,
        budget_snapshot=budget_snapshot,
        upcoming_deposits=upcoming_deposits,
        today=today,
        warnings=warnings,
    )


_WEDDING_ID_ENDPOINTS = {
    "budget.budget",
    "vendors.vendors",
    "checklist.checklist",
    "seating.seating",
    "wedding.wedding_detail",
}


@wedding_bp.route("/wedding/<int:wedding_id>/activate", methods=["POST"])
@login_required
def activate_wedding(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    session["active_wedding_id"] = wedding.id
    next_ep = request.form.get("next_endpoint", "")
    if next_ep in _WEDDING_ID_ENDPOINTS:
        try:
            return redirect(url_for(next_ep, wedding_id=wedding.id))
        except Exception:
            pass
    return redirect(url_for("wedding.dashboard"))


@wedding_bp.route("/wedding/new", methods=["GET", "POST"])
@login_required
def create_wedding():
    if request.method == "POST":
        # Collect and validate required fields
        partner1_name = request.form.get("partner1_name", "").strip()
        partner2_name = request.form.get("partner2_name", "").strip()
        wedding_date_s = request.form.get("wedding_date", "").strip()
        location = request.form.get("location", "").strip()
        venue_name = request.form.get("venue_name", "").strip()
        style = request.form.get("style", "").strip()
        primary_color = request.form.get("primary_color", "").strip()
        secondary_color = request.form.get("secondary_color", "").strip()

        errors = []
        if not partner1_name:
            errors.append("Partner 1 name is required.")
        if not partner2_name:
            errors.append("Partner 2 name is required.")
        if not wedding_date_s:
            errors.append("Wedding date is required.")
        if not location:
            errors.append("Location is required.")
        if not venue_name:
            errors.append("Venue name is required.")
        if style not in WEDDING_STYLES:
            errors.append("Please select a valid wedding style.")
        if not _HEX_COLOR.match(primary_color):
            errors.append("Primary color must be a valid hex color (e.g. #ff5733).")
        if not _HEX_COLOR.match(secondary_color):
            errors.append("Secondary color must be a valid hex color (e.g. #ff5733).")

        wedding_date = None
        if wedding_date_s and not errors:
            try:
                wedding_date = date.fromisoformat(wedding_date_s)
            except ValueError:
                errors.append("Invalid wedding date format.")

        if errors:
            for msg in errors:
                flash(msg, "danger")
            return render_template("wedding/create.html")

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
            flash("Something went wrong saving your wedding. Please try again.", "danger")
            return render_template("wedding/create.html")

        # Seed default checklist
        try:
            from app.services.checklist_service import create_default_checklist

            create_default_checklist(wedding.id, wedding.wedding_date)
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Seed default budget categories
        try:
            from app.services.budget_service import create_default_budget

            create_default_budget(wedding.id)
            db.session.commit()
        except Exception:
            db.session.rollback()  # non-fatal — wedding still created

        flash(f"{partner1_name} & {partner2_name}'s wedding has been created!", "success")
        return redirect(url_for("wedding.dashboard"))

    return render_template("wedding/create.html")


_GUEST_RSVP_DB = {"accepted": "confirmed", "pending": "pending", "declined": "declined"}
_PER_PAGE = 50


@wedding_bp.route("/wedding/<int:wedding_id>")
@login_required
def wedding_detail(wedding_id):
    wedding = get_wedding_or_403(wedding_id)

    # Stats always computed on the full guest list
    guests = wedding.guests
    total = len(guests)
    accepted = sum(1 for g in guests if g.rsvp_status == "confirmed")
    declined = sum(1 for g in guests if g.rsvp_status == "declined")
    pending = sum(1 for g in guests if g.rsvp_status == "pending")
    responded = accepted + declined

    meal_counts = defaultdict(int)
    for g in guests:
        if g.meal_preference:
            meal_counts[g.meal_preference] += 1

    guest_stats = {
        "total": total,
        "accepted": accepted,
        "declined": declined,
        "pending": pending,
        "responded": responded,
        "response_rate": round(responded / total * 100) if total else 0,
        "dietary_count": sum(
            1 for g in guests if g.meal_preference and g.meal_preference != "Standard"
        ),
        "meal_counts": dict(sorted(meal_counts.items())),
        "no_meal": sum(1 for g in guests if not g.meal_preference),
    }

    group_stats = defaultdict(lambda: {"total": 0, "accepted": 0, "pending": 0, "declined": 0})
    for g in guests:
        key = g.group_name or "Ungrouped"
        group_stats[key]["total"] += 1
        if g.rsvp_status == "confirmed":
            group_stats[key]["accepted"] += 1
        elif g.rsvp_status == "declined":
            group_stats[key]["declined"] += 1
        else:
            group_stats[key]["pending"] += 1
    group_stats = dict(sorted(group_stats.items()))

    # Filtered + paginated guest query for the table
    search_q = request.args.get("search", "").strip()
    group_filter = request.args.get("group", "").strip()
    rsvp_filter = request.args.get("rsvp", "").strip()
    page = request.args.get("page", 1, type=int)

    q = Guest.query.filter_by(wedding_id=wedding_id)
    if search_q:
        q = q.filter(
            db.or_(
                Guest.full_name.ilike(f"%{search_q}%"),
                Guest.email.ilike(f"%{search_q}%"),
            )
        )
    if group_filter:
        q = q.filter(Guest.group_name == group_filter)
    db_rsvp = _GUEST_RSVP_DB.get(rsvp_filter)
    if db_rsvp:
        q = q.filter(Guest.rsvp_status == db_rsvp)

    guests_page = q.order_by(Guest.full_name).paginate(
        page=page, per_page=_PER_PAGE, error_out=False
    )
    all_groups = sorted(set(g.group_name for g in guests if g.group_name))

    theme = None
    if wedding.ai_generated_theme:
        with contextlib.suppress(ValueError, TypeError):
            theme = json.loads(wedding.ai_generated_theme)

    today = date.today()
    days_until = (wedding.wedding_date - today).days if wedding.wedding_date else None

    checklist_items = [
        ("Set wedding date", bool(wedding.wedding_date)),
        ("Choose venue", bool(wedding.venue_name)),
        ("Generate AI theme", bool(wedding.ai_generated_theme)),
        ("Select accent colour", theme is not None and bool(theme.get("selected_colour"))),
        ("Add guest list", total > 0),
        ("Create invitation PDF", bool(wedding.designs)),
    ]
    checklist_done = sum(1 for _, v in checklist_items if v)
    checklist_pct = round(checklist_done / len(checklist_items) * 100)

    return render_template(
        "wedding/detail.html",
        wedding=wedding,
        guest_stats=guest_stats,
        group_stats=group_stats,
        theme=theme,
        days_until=days_until,
        checklist_items=checklist_items,
        checklist_pct=checklist_pct,
        guests_page=guests_page,
        search_q=search_q,
        group_filter=group_filter,
        rsvp_filter=rsvp_filter,
        all_groups=all_groups,
        total=total,
        today=today,
    )


@wedding_bp.route("/wedding/<int:wedding_id>/edit", methods=["GET", "POST"])
@login_required
def edit_wedding(wedding_id):
    wedding = get_wedding_or_403(wedding_id)

    if request.method == "POST":
        partner1_name = request.form.get("partner1_name", "").strip()
        partner2_name = request.form.get("partner2_name", "").strip()
        wedding_date_s = request.form.get("wedding_date", "").strip()
        location = request.form.get("location", "").strip()
        venue_name = request.form.get("venue_name", "").strip()
        style = request.form.get("style", "").strip()
        primary_color = request.form.get("primary_color", "").strip()
        secondary_color = request.form.get("secondary_color", "").strip()

        errors = []
        if not partner1_name:
            errors.append("Partner 1 name is required.")
        if not partner2_name:
            errors.append("Partner 2 name is required.")
        if not wedding_date_s:
            errors.append("Wedding date is required.")
        if not location:
            errors.append("Location is required.")
        if not venue_name:
            errors.append("Venue name is required.")
        if style not in WEDDING_STYLES:
            errors.append("Please select a valid wedding style.")
        if not _HEX_COLOR.match(primary_color):
            errors.append("Primary color must be a valid hex color (e.g. #ff5733).")
        if not _HEX_COLOR.match(secondary_color):
            errors.append("Secondary color must be a valid hex color (e.g. #ff5733).")

        wedding_date = None
        if wedding_date_s and not errors:
            try:
                wedding_date = date.fromisoformat(wedding_date_s)
            except ValueError:
                errors.append("Invalid wedding date format.")

        if errors:
            for msg in errors:
                flash(msg, "danger")
            return render_template("wedding/edit.html", wedding=wedding)

        wedding.partner1_name = partner1_name
        wedding.partner2_name = partner2_name
        wedding.wedding_date = wedding_date
        wedding.location = location
        wedding.venue_name = venue_name
        wedding.style = style
        wedding.primary_color = primary_color
        wedding.secondary_color = secondary_color
        wedding.rsvp_contact = request.form.get("rsvp_contact", "").strip() or None
        wedding.ai_generated_theme = None  # invalidate theme when details change

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("Something went wrong saving your changes. Please try again.", "danger")
            return render_template("wedding/edit.html", wedding=wedding)

        flash("Wedding updated successfully.", "success")
        return redirect(url_for("wedding.wedding_detail", wedding_id=wedding.id))

    return render_template("wedding/edit.html", wedding=wedding)


_VALID_TONES = {"Romantic", "Formal", "Playful", "Poetic", "Simple"}


@wedding_bp.route("/wedding/<int:wedding_id>/generate-theme", methods=["POST"])
@login_required
def generate_theme(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    tone = request.form.get("tone", "Romantic").strip()
    if tone not in _VALID_TONES:
        tone = "Romantic"
    theme = generate_wedding_theme(
        partner1_name=wedding.partner1_name,
        partner2_name=wedding.partner2_name,
        wedding_date=wedding.wedding_date.strftime("%B %d, %Y"),
        location=wedding.location,
        venue_name=wedding.venue_name,
        style=wedding.style,
        primary_color=wedding.primary_color,
        secondary_color=wedding.secondary_color,
        tone=tone,
    )
    if theme is None:
        flash("Could not generate theme. Please try again later.", "danger")
    else:
        theme["generated_at"] = date.today().strftime("%B %d, %Y")
        theme["tone"] = tone
        wedding.ai_generated_theme = json.dumps(theme)
        try:
            db.session.commit()
            flash("Your AI wedding theme has been generated!", "success")
        except Exception:
            db.session.rollback()
            flash("Theme generated but could not be saved. Please try again.", "danger")
    return redirect(url_for("wedding.wedding_detail", wedding_id=wedding_id, _anchor="invitation"))


@wedding_bp.route("/test-invitation")
def test_invitation():
    return render_template(
        "pdf/invitation.html",
        partner1_name="Sarah",
        partner2_name="Michael",
        wedding_date="Saturday, June 21st, 2025",
        location="Napa Valley, California",
        venue_name="The Grand Vineyard Estate",
        invitation_text="Together with their families\nSarah and Michael\nrequest the honour of your presence\nat the celebration of their marriage",
        tagline="Two hearts, one love",
        primary_color="#8B4513",
        ceremony_time="4:30 PM",
        rsvp_info="June 1st, 2025  ·  sarah.michael@gmail.com",
    )


@wedding_bp.route("/wedding/<int:wedding_id>/invitation-preview")
@login_required
def invitation_preview(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if not wedding.ai_generated_theme:
        return ("", 204)
    theme = json.loads(wedding.ai_generated_theme)
    from app.services.pdf_service import _format_date

    rsvp_date = theme.get("rsvp_info") or None
    rsvp_info = (
        f"{rsvp_date}  ·  {wedding.rsvp_contact}"
        if (rsvp_date and wedding.rsvp_contact)
        else (rsvp_date or None)
    )
    fonts = theme.get("font_suggestions", [])
    sel_idx = theme.get("selected_font_index", 0)
    selected_font = fonts[sel_idx] if fonts and 0 <= sel_idx < len(fonts) else {}
    return render_template(
        "pdf/invitation.html",
        partner1_name=wedding.partner1_name,
        partner2_name=wedding.partner2_name,
        wedding_date=_format_date(wedding.wedding_date),
        location=wedding.location,
        venue_name=wedding.venue_name,
        invitation_text=theme.get("invitation_text", ""),
        tagline=theme.get("tagline", ""),
        primary_color=theme.get("selected_colour") or wedding.primary_color,
        ceremony_time=theme.get("ceremony_time") or None,
        rsvp_info=rsvp_info,
        heading_font=selected_font.get("heading", "Cormorant Garamond"),
        body_font=selected_font.get("body", "Lato"),
    )


@wedding_bp.route("/wedding/<int:wedding_id>/generate-pdf", methods=["POST"])
@login_required
def generate_pdf(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if not wedding.ai_generated_theme:
        flash("Please generate a theme first.", "warning")
        return redirect(url_for("wedding.wedding_detail", wedding_id=wedding_id))
    theme = json.loads(wedding.ai_generated_theme)
    rsvp_date = theme.get("rsvp_info") or None
    rsvp_info = (
        f"{rsvp_date}  ·  {wedding.rsvp_contact}"
        if (rsvp_date and wedding.rsvp_contact)
        else (rsvp_date or None)
    )
    fonts = theme.get("font_suggestions", [])
    sel_idx = theme.get("selected_font_index", 0)
    selected_font = fonts[sel_idx] if fonts and 0 <= sel_idx < len(fonts) else {}
    pdf_path = generate_invitation_pdf(
        wedding,
        theme,
        ceremony_time=theme.get("ceremony_time") or None,
        rsvp_info=rsvp_info,
        primary_color=theme.get("selected_colour") or wedding.primary_color,
        heading_font=selected_font.get("heading", "Cormorant Garamond"),
        body_font=selected_font.get("body", "Lato"),
    )
    if pdf_path:
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"invitation_{wedding.partner1_name}_{wedding.partner2_name}.pdf",
        )
    flash("PDF generation failed.", "danger")
    return redirect(url_for("wedding.wedding_detail", wedding_id=wedding_id))


@wedding_bp.route("/wedding/<int:wedding_id>/select-colour", methods=["POST"])
@login_required
def select_colour(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if not wedding.ai_generated_theme:
        flash("Generate a theme first.", "warning")
        return redirect(url_for("wedding.wedding_detail", wedding_id=wedding_id))
    theme = json.loads(wedding.ai_generated_theme)
    hex_colour = request.form.get("hex_colour", "").strip()
    if not _HEX_COLOR.match(hex_colour):
        flash("Invalid colour value.", "danger")
        return redirect(
            url_for("wedding.wedding_detail", wedding_id=wedding_id, _anchor="invitation")
        )
    theme["selected_colour"] = hex_colour
    wedding.ai_generated_theme = json.dumps(theme)
    try:
        db.session.commit()
        flash("Colour applied to your invitation.", "success")
    except Exception:
        db.session.rollback()
        flash("Could not save colour selection. Please try again.", "danger")
    return redirect(url_for("wedding.wedding_detail", wedding_id=wedding_id, _anchor="invitation"))


@wedding_bp.route("/wedding/<int:wedding_id>/select-font", methods=["POST"])
@login_required
def select_font(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if not wedding.ai_generated_theme:
        flash("Generate a theme first.", "warning")
        return redirect(url_for("wedding.wedding_detail", wedding_id=wedding_id))
    theme = json.loads(wedding.ai_generated_theme)
    font_index = request.form.get("font_index", type=int, default=0)
    fonts = theme.get("font_suggestions", [])
    if 0 <= font_index < len(fonts):
        theme["selected_font_index"] = font_index
        wedding.ai_generated_theme = json.dumps(theme)
        try:
            db.session.commit()
            flash("Font pairing applied to your invitation.", "success")
        except Exception:
            db.session.rollback()
            flash("Could not save font selection. Please try again.", "danger")
    return redirect(url_for("wedding.wedding_detail", wedding_id=wedding_id, _anchor="invitation"))


@wedding_bp.route("/wedding/<int:wedding_id>/save-wording", methods=["POST"])
@login_required
def save_wording(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if not wedding.ai_generated_theme:
        return {"error": "No theme found"}, 400
    theme = json.loads(wedding.ai_generated_theme)
    text = request.form.get("invitation_text", "").strip()
    if not text:
        return {"error": "Empty wording"}, 400
    theme["invitation_text"] = text
    wedding.ai_generated_theme = json.dumps(theme)
    try:
        db.session.commit()
        return {"ok": True}
    except Exception:
        db.session.rollback()
        return {"error": "Could not save"}, 500


@wedding_bp.route("/wedding/<int:wedding_id>/delete", methods=["POST"])
@login_required
def delete_wedding(wedding_id):
    wedding = get_wedding_or_403(wedding_id)

    name = f"{wedding.partner1_name} & {wedding.partner2_name}"
    try:
        db.session.delete(wedding)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Something went wrong deleting the wedding. Please try again.", "danger")
        return redirect(url_for("wedding.wedding_detail", wedding_id=wedding_id))

    flash(f"{name}'s wedding has been deleted.", "success")
    return redirect(url_for("wedding.dashboard"))
