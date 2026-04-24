import contextlib
from datetime import UTC, datetime
from datetime import date as date_type

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import BudgetCategory, Expense
from app.routes.utils import get_budget_category_or_403, get_expense_or_403, get_wedding_or_403

budget_bp = Blueprint("budget", __name__)

_VENDOR_CAT_KEYWORDS = {
    "Venue": ["venue"],
    "Catering": ["cater", "food", "drink"],
    "Photography": ["photo"],
    "Videography": ["video", "film"],
    "Flowers": ["flower", "floral", "decor", "bouquet"],
    "Music": ["music", "dj", "band", "entertain"],
    "Hair & Makeup": ["hair", "makeup", "beauty", "spa"],
    "Transport": ["transport", "car", "transfer"],
    "Cake": ["cake", "dessert", "sweet"],
    "Stationery": ["station", "invite", "print"],
    "Officiant": ["ceremony", "other"],
    "Other": ["misc", "other"],
}


def find_matching_category(wedding_id, vendor_category):
    """Return the best-matching BudgetCategory for a vendor category, or None."""
    categories = BudgetCategory.query.filter_by(wedding_id=wedding_id).all()
    if not categories:
        return None
    # Exact match first (when vendor category IS a budget category name)
    for cat in categories:
        if cat.name == vendor_category:
            return cat
    # Fuzzy keyword fallback
    keywords = _VENDOR_CAT_KEYWORDS.get(vendor_category, ["other", "misc"])
    for cat in categories:
        name_lower = cat.name.lower()
        for kw in keywords:
            if kw in name_lower:
                return cat
    return categories[0]


TEMPLATES = {
    "rustic": [
        ("Barn/Venue Hire", 0.18, "#a8c890"),
        ("Catering & Drinks", 0.32, "#e8a87c"),
        ("Photography", 0.10, "#c8a878"),
        ("Flowers & Greenery", 0.12, "#90b878"),
        ("Attire", 0.08, "#d4b898"),
        ("Music", 0.05, "#c9687a"),
        ("Handcrafted Decor", 0.06, "#b8a890"),
        ("Transport", 0.03, "#a8b8a0"),
        ("Stationery", 0.03, "#c8b8a8"),
        ("Miscellaneous", 0.03, "#b0b0a8"),
    ],
    "modern": [
        ("Venue", 0.28, "#8a9bb8"),
        ("Catering & Bar", 0.30, "#e8a87c"),
        ("Photography & Video", 0.12, "#a8c8d8"),
        ("Minimal Floral", 0.08, "#a8d8a8"),
        ("Attire", 0.08, "#d4d4d4"),
        ("DJ & Lighting", 0.06, "#c9687a"),
        ("Transport", 0.03, "#b8b8c8"),
        ("Stationery", 0.03, "#c0c8d0"),
        ("Hair & Makeup", 0.02, "#e8c4b8"),
    ],
    "luxury": [
        ("Venue", 0.30, "#c9b870"),
        ("Catering & Champagne", 0.28, "#e8a87c"),
        ("Photography & Video", 0.12, "#a8c8d8"),
        ("Flowers & Styling", 0.10, "#d4a8d8"),
        ("Couture Attire", 0.08, "#f0d4a8"),
        ("Live Entertainment", 0.05, "#c9687a"),
        ("Transport", 0.03, "#8a9bb8"),
        ("Stationery & Gifts", 0.02, "#a8b8c8"),
        ("Hair, Makeup & Spa", 0.02, "#e8c4b8"),
    ],
    "beach": [
        ("Venue & Permits", 0.20, "#7cb8e8"),
        ("Catering", 0.30, "#e8a87c"),
        ("Photography", 0.12, "#a8d8a8"),
        ("Flowers & Decor", 0.10, "#d4a8d8"),
        ("Attire", 0.08, "#f0d4a8"),
        ("Music & Entertainment", 0.06, "#c9687a"),
        ("Transport", 0.04, "#8a9bb8"),
        ("Stationery & Invites", 0.03, "#a8c8d8"),
        ("Hair & Makeup", 0.04, "#e8c4a8"),
        ("Miscellaneous", 0.03, "#b8b8a8"),
    ],
    "vintage": [
        ("Venue & Hall Hire", 0.22, "#c8b89a"),
        ("Catering & Tea", 0.28, "#e8a87c"),
        ("Photography", 0.12, "#c8a878"),
        ("Antique Floral", 0.10, "#d4a8d8"),
        ("Vintage Attire", 0.10, "#f0d4a8"),
        ("Live Band", 0.06, "#c9687a"),
        ("Vintage Transport", 0.05, "#a8b098"),
        ("Stationery", 0.04, "#c8b8a8"),
        ("Hair & Makeup", 0.03, "#e8c4b8"),
    ],
    "minimalist": [
        ("Venue", 0.30, "#b8b8b8"),
        ("Catering", 0.32, "#e8a87c"),
        ("Photography", 0.15, "#a8b8c8"),
        ("Simple Florals", 0.08, "#c8d8c0"),
        ("Attire", 0.08, "#d8d8d0"),
        ("Music", 0.04, "#c9687a"),
        ("Stationery", 0.03, "#c0c8c8"),
    ],
}


def _utcnow():
    return datetime.now(UTC)


def _budget_totals(wedding):
    """Return (total_estimated, total_actual_paid, total_allocated) for a wedding."""
    cats = wedding.budget_categories
    total_estimated = sum(e.estimated_cost or 0 for e in wedding.expenses)
    total_actual_paid = sum(e.actual_cost or 0 for e in wedding.expenses if e.is_paid)
    total_actual_all = sum(e.actual_cost or 0 for e in wedding.expenses)
    total_allocated = sum(cat.allocated_amount or 0 for cat in cats)
    return total_estimated, total_actual_paid, total_actual_all, total_allocated


# ── Main budget page ──────────────────────────────────────────────────
@budget_bp.route("/wedding/<int:wedding_id>/budget")
@login_required
def budget(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    categories = (
        BudgetCategory.query.filter_by(wedding_id=wedding_id)
        .order_by(BudgetCategory.created_at)
        .all()
    )

    total_estimated, total_actual_paid, total_actual_all, total_allocated = _budget_totals(wedding)
    total_budget = wedding.total_budget or 0
    remaining = total_budget - total_actual_paid

    # Upcoming payments: unpaid expenses with a due_date, sorted soonest first
    upcoming = (
        Expense.query.filter_by(wedding_id=wedding_id, is_paid=False)
        .filter(Expense.due_date.isnot(None))
        .order_by(Expense.due_date)
        .all()
    )

    # Chart.js data
    chart_labels = [c.name for c in categories]
    chart_colors = [c.color for c in categories]
    chart_allocated = [c.allocated_amount or 0 for c in categories]
    chart_estimated = [sum(e.estimated_cost or 0 for e in c.expenses) for c in categories]
    chart_actual = [sum(e.actual_cost or 0 for e in c.expenses if e.is_paid) for c in categories]

    booked_vendor_names = [v.business_name for v in wedding.vendors if v.status == "booked"]

    return render_template(
        "wedding/budget.html",
        wedding=wedding,
        categories=categories,
        total_budget=total_budget,
        total_estimated=total_estimated,
        total_actual_paid=total_actual_paid,
        total_actual_all=total_actual_all,
        total_allocated=total_allocated,
        remaining=remaining,
        upcoming=upcoming,
        chart_labels=chart_labels,
        chart_colors=chart_colors,
        chart_allocated=chart_allocated,
        chart_estimated=chart_estimated,
        chart_actual=chart_actual,
        date_today=date_type.today(),
        booked_vendor_names=booked_vendor_names,
    )


# ── Set total budget (JSON) ───────────────────────────────────────────
@budget_bp.route("/wedding/<int:wedding_id>/budget/set-total", methods=["POST"])
@login_required
def set_total(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    try:
        if request.is_json:
            amount = float(request.json.get("amount", 0) or 0)
        else:
            amount = float(request.form.get("amount", 0) or 0)
        amount = max(0, amount)
    except (ValueError, TypeError):
        return jsonify({"ok": False, "error": "Invalid amount"}), 400

    old_total = wedding.total_budget or 0
    wedding.total_budget = amount

    from app.services.budget_service import scale_existing_categories

    scale_existing_categories(wedding_id, old_total, amount)

    try:
        db.session.commit()
        _, total_actual_paid, _, _ = _budget_totals(wedding)
        remaining = amount - total_actual_paid
        return jsonify(
            {
                "ok": True,
                "total_budget": amount,
                "remaining": remaining,
                "pct": round(total_actual_paid / amount * 100) if amount else 0,
            }
        )
    except Exception:
        db.session.rollback()
        return jsonify({"ok": False, "error": "DB error"}), 500


# ── Add category ──────────────────────────────────────────────────────
@budget_bp.route("/wedding/<int:wedding_id>/budget/category/add", methods=["POST"])
@login_required
def add_category(wedding_id):
    get_wedding_or_403(wedding_id)
    name = request.form.get("name", "").strip()
    color = request.form.get("color", "#c9687a").strip()
    try:
        allocated = float(request.form.get("allocated_amount", 0) or 0)
    except ValueError:
        allocated = 0

    if not name:
        flash("Category name is required.", "danger")
        return redirect(url_for("budget.budget", wedding_id=wedding_id))

    cat = BudgetCategory(wedding_id=wedding_id, name=name, allocated_amount=allocated, color=color)
    db.session.add(cat)
    try:
        db.session.commit()
        flash(f'Category "{name}" added.', "success")
    except Exception:
        db.session.rollback()
        flash("Could not add category.", "danger")
    return redirect(url_for("budget.budget", wedding_id=wedding_id))


# ── Edit category ─────────────────────────────────────────────────────
@budget_bp.route("/budget/category/<int:cat_id>/edit", methods=["POST"])
@login_required
def edit_category(cat_id):
    cat = get_budget_category_or_403(cat_id)
    name = request.form.get("name", "").strip()
    try:
        allocated = float(request.form.get("allocated_amount", cat.allocated_amount) or 0)
    except ValueError:
        allocated = cat.allocated_amount
    color = request.form.get("color", cat.color).strip()

    if not name:
        flash("Category name is required.", "danger")
        return redirect(url_for("budget.budget", wedding_id=cat.wedding_id))

    cat.name = name
    cat.allocated_amount = allocated
    cat.color = color
    try:
        db.session.commit()
        flash("Category updated.", "success")
    except Exception:
        db.session.rollback()
        flash("Could not update category.", "danger")
    return redirect(url_for("budget.budget", wedding_id=cat.wedding_id))


# ── Delete category ───────────────────────────────────────────────────
@budget_bp.route("/budget/category/<int:cat_id>/delete", methods=["POST"])
@login_required
def delete_category(cat_id):
    cat = get_budget_category_or_403(cat_id)
    wedding_id = cat.wedding_id
    db.session.delete(cat)
    try:
        db.session.commit()
        flash("Category and all its expenses deleted.", "success")
    except Exception:
        db.session.rollback()
        flash("Could not delete category.", "danger")
    return redirect(url_for("budget.budget", wedding_id=wedding_id))


# ── Add expense ───────────────────────────────────────────────────────
@budget_bp.route("/wedding/<int:wedding_id>/budget/expense/add", methods=["POST"])
@login_required
def add_expense(wedding_id):
    get_wedding_or_403(wedding_id)
    title = request.form.get("title", "").strip()
    cat_id_raw = request.form.get("category_id", "").strip()
    notes = request.form.get("notes", "").strip() or None
    anchor = request.form.get("anchor", "")

    if not title:
        flash("Expense title is required.", "danger")
        return redirect(url_for("budget.budget", wedding_id=wedding_id))

    try:
        estimated = float(request.form.get("estimated_cost", 0) or 0)
    except ValueError:
        estimated = 0
    actual_raw = request.form.get("actual_cost", "").strip()
    actual = None
    if actual_raw:
        try:
            actual = float(actual_raw)
        except ValueError:
            actual = None

    cat_id = None
    if cat_id_raw:
        try:
            cat_id = int(cat_id_raw)
            # Verify belongs to this wedding
            cat = BudgetCategory.query.get(cat_id)
            if not cat or cat.wedding_id != wedding_id:
                cat_id = None
        except ValueError:
            cat_id = None

    due_date = None
    due_raw = request.form.get("due_date", "").strip()
    if due_raw:
        with contextlib.suppress(ValueError):
            due_date = date_type.fromisoformat(due_raw)

    expense = Expense(
        wedding_id=wedding_id,
        category_id=cat_id,
        title=title,
        estimated_cost=estimated,
        actual_cost=actual,
        due_date=due_date,
        notes=notes,
    )
    db.session.add(expense)
    try:
        db.session.commit()
        # Connection 4: check budget completion after adding expense
        from app.utils.connections import check_budget_completion

        check_budget_completion(wedding_id)
    except Exception:
        db.session.rollback()
        flash("Could not add expense.", "danger")

    redir = url_for("budget.budget", wedding_id=wedding_id)
    if anchor:
        redir += "#" + anchor
    return redirect(redir)


# ── Edit expense ──────────────────────────────────────────────────────
@budget_bp.route("/budget/expense/<int:expense_id>/edit", methods=["POST"])
@login_required
def edit_expense(expense_id):
    expense = get_expense_or_403(expense_id)
    title = request.form.get("title", "").strip()
    if not title:
        flash("Expense title is required.", "danger")
        return redirect(url_for("budget.budget", wedding_id=expense.wedding_id))

    with contextlib.suppress(ValueError):
        expense.estimated_cost = float(request.form.get("estimated_cost", 0) or 0)
    actual_raw = request.form.get("actual_cost", "").strip()
    expense.actual_cost = float(actual_raw) if actual_raw else None

    due_raw = request.form.get("due_date", "").strip()
    expense.due_date = date_type.fromisoformat(due_raw) if due_raw else None

    cat_id_raw = request.form.get("category_id", "").strip()
    if cat_id_raw:
        try:
            cid = int(cat_id_raw)
            cat = BudgetCategory.query.get(cid)
            if cat and cat.wedding_id == expense.wedding_id:
                expense.category_id = cid
        except ValueError:
            pass
    else:
        expense.category_id = None

    expense.title = title
    expense.notes = request.form.get("notes", "").strip() or None

    try:
        db.session.commit()
        # Connection 4: check budget completion after editing expense
        from app.utils.connections import check_budget_completion

        check_budget_completion(expense.wedding_id)
        flash("Expense updated.", "success")
    except Exception:
        db.session.rollback()
        flash("Could not update expense.", "danger")
    return redirect(url_for("budget.budget", wedding_id=expense.wedding_id))


# ── Delete expense ────────────────────────────────────────────────────
@budget_bp.route("/budget/expense/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete_expense(expense_id):
    expense = get_expense_or_403(expense_id)
    wedding_id = expense.wedding_id
    db.session.delete(expense)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Could not delete expense.", "danger")
    return redirect(url_for("budget.budget", wedding_id=wedding_id))


# ── Toggle paid (AJAX) ────────────────────────────────────────────────
@budget_bp.route("/budget/expense/<int:expense_id>/toggle-paid", methods=["POST"])
@login_required
def toggle_paid(expense_id):
    expense = get_expense_or_403(expense_id)
    expense.is_paid = not expense.is_paid
    expense.paid_date = date_type.today() if expense.is_paid else None
    try:
        db.session.commit()

        # Connection 2: if all booked vendor deposits are now paid, complete
        # any 'deposits' checklist task
        from app.models import Vendor
        from app.utils.connections import auto_complete_task_by_keyword

        booked_vendors = Vendor.query.filter_by(
            wedding_id=expense.wedding_id,
            status="booked",
        ).all()
        if booked_vendors and all(v.deposit_paid for v in booked_vendors):
            auto_complete_task_by_keyword(
                expense.wedding_id,
                ["deposit", "pay deposit", "deposits"],
            )

        # Connection 4: check if budget spend has reached total budget
        from app.utils.connections import check_budget_completion

        check_budget_completion(expense.wedding_id)

        _, total_actual_paid, total_actual_all, _ = _budget_totals(expense.wedding)
        total_budget = expense.wedding.total_budget or 0
        return jsonify(
            {
                "ok": True,
                "is_paid": expense.is_paid,
                "paid_date": expense.paid_date.isoformat() if expense.paid_date else None,
                "total_actual_paid": total_actual_paid,
                "total_actual_all": total_actual_all,
                "remaining": total_budget - total_actual_paid,
                "pct": round(total_actual_paid / total_budget * 100) if total_budget else 0,
            }
        )
    except Exception:
        db.session.rollback()
        return jsonify({"ok": False}), 500


# ── Apply template ───────────────────────────────────────────────────
@budget_bp.route("/wedding/<int:wedding_id>/budget/apply-template", methods=["POST"])
@login_required
def apply_template(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if wedding.budget_categories:
        return jsonify({"success": False, "message": "You already have categories"}), 400
    data = request.get_json(force=True, silent=True) or {}
    style = data.get("style", "").strip().lower()
    if style not in TEMPLATES:
        return jsonify({"success": False, "message": "Unknown style"}), 400
    base = float(wedding.total_budget or 10000) or 10000
    try:
        for name, pct, color in TEMPLATES[style]:
            allocated = round(base * pct / 10) * 10
            db.session.add(
                BudgetCategory(
                    wedding_id=wedding_id,
                    name=name,
                    allocated_amount=allocated,
                    color=color,
                )
            )
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({"success": False, "message": "Database error"}), 500
    flash(
        "✓ Budget template applied! All amounts are suggestions — adjust them to match your actual plans.",
        "success",
    )
    return jsonify({"success": True, "redirect": url_for("budget.budget", wedding_id=wedding_id)})


# ── Reset budget ──────────────────────────────────────────────────────
@budget_bp.route("/wedding/<int:wedding_id>/budget/reset", methods=["POST"])
@login_required
def reset_budget(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    try:
        for cat in list(wedding.budget_categories):
            db.session.delete(cat)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Could not reset budget.", "danger")
        return redirect(url_for("budget.budget", wedding_id=wedding_id))
    flash("Budget reset. Choose a template to get started.", "success")
    return redirect(url_for("budget.budget", wedding_id=wedding_id))


# ── Budget summary JSON (for overview AJAX) ───────────────────────────
@budget_bp.route("/wedding/<int:wedding_id>/budget/summary")
@login_required
def budget_summary(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    total_estimated, total_actual_paid, total_actual_all, total_allocated = _budget_totals(wedding)
    total_budget = wedding.total_budget or 0
    by_cat = {}
    for cat in wedding.budget_categories:
        est = sum(e.estimated_cost or 0 for e in cat.expenses)
        paid = sum(e.actual_cost or 0 for e in cat.expenses if e.is_paid)
        by_cat[cat.name] = {
            "allocated": cat.allocated_amount,
            "estimated": est,
            "actual": paid,
            "color": cat.color,
        }
    return jsonify(
        {
            "total_budget": total_budget,
            "total_estimated": total_estimated,
            "total_actual_paid": total_actual_paid,
            "remaining": total_budget - total_actual_paid,
            "pct": round(total_actual_paid / total_budget * 100) if total_budget else 0,
            "by_category": by_cat,
        }
    )
