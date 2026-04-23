import contextlib
from collections import defaultdict
from datetime import UTC, date, datetime

from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import CHECKLIST_CATEGORIES, CHECKLIST_PRIORITIES, ChecklistItem, Vendor
from app.routes.utils import get_checklist_item_or_403, get_wedding_or_403
from app.utils.connections import VENDOR_TO_TASK

checklist_bp = Blueprint("checklist", __name__)


def _utcnow():
    return datetime.now(UTC)


# ── Checklist page ────────────────────────────────────────────────────
@checklist_bp.route("/wedding/<int:wedding_id>/checklist")
@login_required
def checklist(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    today = date.today()

    items = (
        ChecklistItem.query.filter_by(wedding_id=wedding_id)
        .order_by(ChecklistItem.due_date.asc().nullslast(), ChecklistItem.created_at)
        .all()
    )

    total = len(items)
    completed = sum(1 for i in items if i.is_completed)
    pct = round(completed / total * 100) if total else 0

    overdue_count = sum(
        1 for i in items if not i.is_completed and i.due_date and i.due_date < today
    )

    # Group by category in canonical order
    by_category = defaultdict(list)
    for item in items:
        by_category[item.category or "Other"].append(item)

    items_by_category = []
    for cat in CHECKLIST_CATEGORIES:
        if cat in by_category:
            items_by_category.append((cat, by_category[cat]))
    known = set(CHECKLIST_CATEGORIES)
    for cat, cat_items in by_category.items():
        if cat not in known:
            items_by_category.append((cat, cat_items))

    # ── Vendor context ────────────────────────────────────────────────
    all_vendors = Vendor.query.filter_by(wedding_id=wedding_id).all()

    # Best vendor per category: booked > considering > backup > rejected
    _STATUS_ORDER = ("booked", "considering", "backup", "rejected")
    vendors_by_cat = {}
    for v in all_vendors:
        vendors_by_cat.setdefault(v.category, []).append(v)

    def _best_vendor(cat):
        vlist = vendors_by_cat.get(cat, [])
        for status in _STATUS_ORDER:
            for v in vlist:
                if v.status == status:
                    return v
        return vlist[0] if vlist else None

    # Map each checklist item to its best matched vendor (or None)
    item_vendor_map = {}
    for item in items:
        for cat, keywords in VENDOR_TO_TASK.items():
            if any(kw in item.title.lower() for kw in keywords):
                v = _best_vendor(cat)
                if v:
                    item_vendor_map[item.id] = v
                break

    # ── Combined timeline list (tasks + vendor deposit + balance events) ─
    tl_entries = []
    for item in items:
        if item.due_date:
            tl_entries.append({"kind": "task", "date": item.due_date, "item": item})
    for v in all_vendors:
        if v.deposit_due_date:
            tl_entries.append({"kind": "deposit", "date": v.deposit_due_date, "vendor": v})
        # Balance: compute from fields or from quoted-deposit for pre-feature vendors
        balance_amt = v.final_payment_amount or (
            (v.quoted_price - v.deposit_amount)
            if v.quoted_price and v.deposit_amount and v.quoted_price > v.deposit_amount
            else None
        )
        if balance_amt and not v.final_payment_paid:
            tl_entries.append(
                {
                    "kind": "balance",
                    "date": v.final_payment_due_date,
                    "vendor": v,
                    "balance_amt": balance_amt,
                }
            )

    # Sort: dated entries first (ascending), undated entries last
    tl_combined_dated = sorted(tl_entries, key=lambda x: (x["date"] is None, x["date"] or date.max))
    tl_undated = [i for i in items if not i.due_date]

    return render_template(
        "wedding/checklist.html",
        wedding=wedding,
        items_by_category=items_by_category,
        tl_combined_dated=tl_combined_dated,
        tl_undated=tl_undated,
        item_vendor_map=item_vendor_map,
        total=total,
        completed=completed,
        pct=pct,
        overdue_count=overdue_count,
        today=today,
        categories=CHECKLIST_CATEGORIES,
        priorities=CHECKLIST_PRIORITIES,
    )


# ── Add item ──────────────────────────────────────────────────────────
@checklist_bp.route("/wedding/<int:wedding_id>/checklist/add", methods=["POST"])
@login_required
def add_item(wedding_id):
    get_wedding_or_403(wedding_id)
    is_json = request.is_json
    data = request.get_json(silent=True) or {}

    def get(k, d=""):
        return (data.get(k) or request.form.get(k) or d).strip()

    title = get("title")
    category = get("category", "Other")
    priority = get("priority", "medium")
    notes = get("notes") or None
    due_raw = get("due_date")

    if not title:
        if is_json:
            return jsonify({"error": "Title is required."}), 400
        return redirect(url_for("checklist.checklist", wedding_id=wedding_id))

    if category not in CHECKLIST_CATEGORIES:
        category = "Other"
    if priority not in CHECKLIST_PRIORITIES:
        priority = "medium"

    due_date = None
    if due_raw:
        with contextlib.suppress(ValueError):
            due_date = date.fromisoformat(due_raw)

    item = ChecklistItem(
        wedding_id=wedding_id,
        title=title,
        category=category,
        priority=priority,
        notes=notes,
        due_date=due_date,
    )
    db.session.add(item)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        if is_json:
            return jsonify({"error": "Could not save."}), 500

    if is_json:
        return jsonify({"ok": True, "id": item.id})
    return redirect(url_for("checklist.checklist", wedding_id=wedding_id))


# ── Toggle item ───────────────────────────────────────────────────────
@checklist_bp.route("/checklist/<int:item_id>/toggle", methods=["POST"])
@login_required
def toggle_item(item_id):
    item = get_checklist_item_or_403(item_id)
    item.is_completed = not item.is_completed
    item.completed_at = _utcnow() if item.is_completed else None
    try:
        db.session.commit()
        all_items = ChecklistItem.query.filter_by(wedding_id=item.wedding_id).all()
        total = len(all_items)
        done = sum(1 for i in all_items if i.is_completed)
        return jsonify(
            {
                "ok": True,
                "is_completed": item.is_completed,
                "completed_at": item.completed_at.strftime("%b %-d") if item.completed_at else None,
                "total": total,
                "done": done,
                "pct": round(done / total * 100) if total else 0,
            }
        )
    except Exception:
        db.session.rollback()
        return jsonify({"ok": False, "error": "DB error"}), 500


# ── Edit item ─────────────────────────────────────────────────────────
@checklist_bp.route("/checklist/<int:item_id>/edit", methods=["POST"])
@login_required
def edit_item(item_id):
    item = get_checklist_item_or_403(item_id)
    title = request.form.get("title", "").strip()
    category = request.form.get("category", item.category).strip()
    priority = request.form.get("priority", item.priority).strip()
    notes = request.form.get("notes", "").strip() or None
    due_raw = request.form.get("due_date", "").strip()

    if not title:
        return redirect(url_for("checklist.checklist", wedding_id=item.wedding_id))

    if category not in CHECKLIST_CATEGORIES:
        category = "Other"
    if priority not in CHECKLIST_PRIORITIES:
        priority = "medium"

    if due_raw:
        with contextlib.suppress(ValueError):
            item.due_date = date.fromisoformat(due_raw)
    elif due_raw == "":
        item.due_date = None

    item.title = title
    item.category = category
    item.priority = priority
    item.notes = notes

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    return redirect(url_for("checklist.checklist", wedding_id=item.wedding_id))


# ── Delete item ───────────────────────────────────────────────────────
@checklist_bp.route("/checklist/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_item(item_id):
    item = get_checklist_item_or_403(item_id)
    db.session.delete(item)
    try:
        db.session.commit()
        return jsonify({"ok": True})
    except Exception:
        db.session.rollback()
        return jsonify({"ok": False, "error": "DB error"}), 500
