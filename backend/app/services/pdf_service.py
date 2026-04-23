import os
from datetime import datetime

from flask import current_app, render_template
from weasyprint import HTML

from app import db
from app.models import Design


def _format_date(d):
    """Format a date as 'Saturday, June 21st, 2025'."""
    day = d.day
    suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return d.strftime(f"%A, %B {day}{suffix}, %Y")


def generate_invitation_pdf(
    wedding,
    theme,
    ceremony_time=None,
    rsvp_info=None,
    primary_color=None,
    heading_font="Cormorant Garamond",
    body_font="Lato",
):
    """Render the invitation template and convert to PDF with WeasyPrint.

    Args:
        wedding:       Wedding model instance.
        theme:         Parsed AI theme dict (must contain invitation_text, tagline).
        ceremony_time: Optional time string, e.g. '4:30 PM'.
        rsvp_info:     Optional RSVP string, e.g. 'June 1st · email@example.com'.

    Returns:
        Absolute file path of the saved PDF, or None on failure.
    """
    # ── Render HTML ───────────────────────────────────────────
    try:
        html = render_template(
            "pdf/invitation.html",
            partner1_name=wedding.partner1_name,
            partner2_name=wedding.partner2_name,
            wedding_date=_format_date(wedding.wedding_date),
            location=wedding.location,
            venue_name=wedding.venue_name,
            invitation_text=theme.get("invitation_text", ""),
            tagline=theme.get("tagline", ""),
            primary_color=primary_color or wedding.primary_color,
            ceremony_time=ceremony_time,
            rsvp_info=rsvp_info,
            heading_font=heading_font,
            body_font=body_font,
        )
    except Exception as e:
        print(f"[pdf_service] template render failed: {e}")
        return None

    # ── Resolve uploads directory ─────────────────────────────
    uploads_dir = os.path.join(current_app.root_path, "..", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"invitation_{wedding.id}_{timestamp}.pdf"
    file_path = os.path.abspath(os.path.join(uploads_dir, filename))

    # ── Convert to PDF ────────────────────────────────────────
    try:
        HTML(string=html, base_url=current_app.root_path).write_pdf(file_path)
    except Exception as e:
        print(f"[pdf_service] PDF generation failed: {e}")
        return None

    # ── Persist Design record ─────────────────────────────────
    design = Design(
        wedding_id=wedding.id,
        design_type="invitation",
        html_content=html,
        pdf_file_path=file_path,
    )
    db.session.add(design)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[pdf_service] failed to save Design record: {e}")
        # PDF already written — still return the path

    return file_path
