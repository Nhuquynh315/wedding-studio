from collections import defaultdict
from datetime import date, datetime, timezone

from flask import Blueprint, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import CHECKLIST_CATEGORIES, CHECKLIST_PRIORITIES, ChecklistItem
from app.routes.utils import get_checklist_item_or_403, get_wedding_or_403

checklist_bp = Blueprint('checklist', __name__)


def _utcnow():
    return datetime.now(timezone.utc)


# ── Checklist page ────────────────────────────────────────────────────
@checklist_bp.route('/wedding/<int:wedding_id>/checklist')
@login_required
def checklist(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    today   = date.today()

    items = (ChecklistItem.query
             .filter_by(wedding_id=wedding_id)
             .order_by(ChecklistItem.due_date.asc().nullslast(), ChecklistItem.created_at)
             .all())

    total     = len(items)
    completed = sum(1 for i in items if i.is_completed)
    pct       = round(completed / total * 100) if total else 0

    overdue_count = sum(
        1 for i in items
        if not i.is_completed and i.due_date and i.due_date < today
    )

    # Group by category in canonical order
    by_category = defaultdict(list)
    for item in items:
        by_category[item.category or 'Other'].append(item)

    items_by_category = []
    for cat in CHECKLIST_CATEGORIES:
        if cat in by_category:
            items_by_category.append((cat, by_category[cat]))
    known = set(CHECKLIST_CATEGORIES)
    for cat, cat_items in by_category.items():
        if cat not in known:
            items_by_category.append((cat, cat_items))

    # Pre-sorted items for timeline view: dated asc then undated
    items_dated   = sorted([i for i in items if i.due_date], key=lambda x: x.due_date)
    items_undated = [i for i in items if not i.due_date]
    timeline_items = items_dated + items_undated

    return render_template(
        'wedding/checklist.html',
        wedding=wedding,
        items_by_category=items_by_category,
        timeline_items=timeline_items,
        total=total,
        completed=completed,
        pct=pct,
        overdue_count=overdue_count,
        today=today,
        categories=CHECKLIST_CATEGORIES,
        priorities=CHECKLIST_PRIORITIES,
    )


# ── Add item ──────────────────────────────────────────────────────────
@checklist_bp.route('/wedding/<int:wedding_id>/checklist/add', methods=['POST'])
@login_required
def add_item(wedding_id):
    wedding  = get_wedding_or_403(wedding_id)
    is_json  = request.is_json
    data     = request.get_json(silent=True) or {}
    get      = lambda k, d='': (data.get(k) or request.form.get(k) or d).strip()

    title    = get('title')
    category = get('category', 'Other')
    priority = get('priority', 'medium')
    notes    = get('notes') or None
    due_raw  = get('due_date')

    if not title:
        if is_json:
            return jsonify({'error': 'Title is required.'}), 400
        return redirect(url_for('checklist.checklist', wedding_id=wedding_id))

    if category not in CHECKLIST_CATEGORIES:
        category = 'Other'
    if priority not in CHECKLIST_PRIORITIES:
        priority = 'medium'

    due_date = None
    if due_raw:
        try:
            due_date = date.fromisoformat(due_raw)
        except ValueError:
            pass

    item = ChecklistItem(
        wedding_id=wedding_id,
        title=title, category=category,
        priority=priority, notes=notes, due_date=due_date,
    )
    db.session.add(item)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        if is_json:
            return jsonify({'error': 'Could not save.'}), 500

    if is_json:
        return jsonify({'ok': True, 'id': item.id})
    return redirect(url_for('checklist.checklist', wedding_id=wedding_id))


# ── Toggle item ───────────────────────────────────────────────────────
@checklist_bp.route('/checklist/<int:item_id>/toggle', methods=['POST'])
@login_required
def toggle_item(item_id):
    item = get_checklist_item_or_403(item_id)
    item.is_completed = not item.is_completed
    item.completed_at = _utcnow() if item.is_completed else None
    try:
        db.session.commit()
        all_items = ChecklistItem.query.filter_by(wedding_id=item.wedding_id).all()
        total = len(all_items)
        done  = sum(1 for i in all_items if i.is_completed)
        return jsonify({
            'ok':          True,
            'is_completed': item.is_completed,
            'completed_at': item.completed_at.strftime('%b %-d') if item.completed_at else None,
            'total': total,
            'done':  done,
            'pct':   round(done / total * 100) if total else 0,
        })
    except Exception:
        db.session.rollback()
        return jsonify({'ok': False, 'error': 'DB error'}), 500


# ── Edit item ─────────────────────────────────────────────────────────
@checklist_bp.route('/checklist/<int:item_id>/edit', methods=['POST'])
@login_required
def edit_item(item_id):
    item     = get_checklist_item_or_403(item_id)
    title    = request.form.get('title', '').strip()
    category = request.form.get('category', item.category).strip()
    priority = request.form.get('priority', item.priority).strip()
    notes    = request.form.get('notes', '').strip() or None
    due_raw  = request.form.get('due_date', '').strip()

    if not title:
        return redirect(url_for('checklist.checklist', wedding_id=item.wedding_id))

    if category not in CHECKLIST_CATEGORIES:
        category = 'Other'
    if priority not in CHECKLIST_PRIORITIES:
        priority = 'medium'

    if due_raw:
        try:
            item.due_date = date.fromisoformat(due_raw)
        except ValueError:
            pass
    elif due_raw == '':
        item.due_date = None

    item.title    = title
    item.category = category
    item.priority = priority
    item.notes    = notes

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    return redirect(url_for('checklist.checklist', wedding_id=item.wedding_id))


# ── Delete item ───────────────────────────────────────────────────────
@checklist_bp.route('/checklist/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item = get_checklist_item_or_403(item_id)
    db.session.delete(item)
    try:
        db.session.commit()
        return jsonify({'ok': True})
    except Exception:
        db.session.rollback()
        return jsonify({'ok': False, 'error': 'DB error'}), 500
