from collections import defaultdict
from datetime import datetime, timezone

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
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
    items   = (ChecklistItem.query
               .filter_by(wedding_id=wedding_id)
               .order_by(ChecklistItem.due_date.asc().nullslast(), ChecklistItem.created_at)
               .all())

    total = len(items)
    done  = sum(1 for i in items if i.is_completed)
    pct   = round(done / total * 100) if total else 0

    # Group by category preserving canonical order
    by_category = defaultdict(list)
    for item in items:
        by_category[item.category].append(item)

    ordered_groups = [
        (cat, by_category[cat])
        for cat in CHECKLIST_CATEGORIES
        if cat in by_category
    ]
    # Include any unlisted categories that exist in the data
    known = set(CHECKLIST_CATEGORIES)
    for cat, cat_items in by_category.items():
        if cat not in known:
            ordered_groups.append((cat, cat_items))

    return render_template(
        'wedding/checklist.html',
        wedding=wedding,
        items=items,
        ordered_groups=ordered_groups,
        total=total,
        done=done,
        pct=pct,
        categories=CHECKLIST_CATEGORIES,
        priorities=CHECKLIST_PRIORITIES,
    )


# ── Add item ──────────────────────────────────────────────────────────
@checklist_bp.route('/wedding/<int:wedding_id>/checklist/add', methods=['POST'])
@login_required
def add_item(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    is_json = request.is_json
    data     = request.get_json(silent=True) or {}
    get      = lambda k, d='': (data.get(k) or request.form.get(k) or d).strip()

    title    = get('title')
    category = get('category', 'Other')
    priority = get('priority', 'medium')
    notes    = get('notes') or None
    due_raw  = get('due_date')

    if not title:
        if is_json:
            return {'error': 'Task title is required.'}, 400
        flash('Task title is required.', 'danger')
        return redirect(url_for('checklist.checklist', wedding_id=wedding_id))

    if category not in CHECKLIST_CATEGORIES:
        category = 'Other'
    if priority not in CHECKLIST_PRIORITIES:
        priority = 'medium'

    due_date = None
    if due_raw:
        try:
            from datetime import date
            due_date = date.fromisoformat(due_raw)
        except ValueError:
            if is_json:
                return {'error': 'Invalid due date.'}, 400
            flash('Invalid due date.', 'danger')
            return redirect(url_for('checklist.checklist', wedding_id=wedding_id))

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
            return {'error': 'Could not add task. Please try again.'}, 500
        flash('Could not add task. Please try again.', 'danger')
    if is_json:
        return {'ok': True, 'id': item.id}
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
        # Recalculate wedding-level stats for the response
        all_items = ChecklistItem.query.filter_by(wedding_id=item.wedding_id).all()
        total = len(all_items)
        done  = sum(1 for i in all_items if i.is_completed)
        return jsonify({
            'ok': True,
            'is_completed': item.is_completed,
            'total': total,
            'done': done,
            'pct': round(done / total * 100) if total else 0,
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
        flash('Task title is required.', 'danger')
        return redirect(url_for('checklist.checklist', wedding_id=item.wedding_id))

    if category not in CHECKLIST_CATEGORIES:
        category = 'Other'
    if priority not in CHECKLIST_PRIORITIES:
        priority = 'medium'

    due_date = item.due_date
    if due_raw:
        try:
            from datetime import date
            due_date = date.fromisoformat(due_raw)
        except ValueError:
            flash('Invalid due date.', 'danger')
            return redirect(url_for('checklist.checklist', wedding_id=item.wedding_id))
    elif due_raw == '':
        due_date = None

    item.title    = title
    item.category = category
    item.priority = priority
    item.notes    = notes
    item.due_date = due_date

    try:
        db.session.commit()
        flash('Task updated.', 'success')
    except Exception:
        db.session.rollback()
        flash('Could not update task. Please try again.', 'danger')
    return redirect(url_for('checklist.checklist', wedding_id=item.wedding_id))


# ── Delete item ───────────────────────────────────────────────────────
@checklist_bp.route('/checklist/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item = get_checklist_item_or_403(item_id)
    wedding_id = item.wedding_id
    db.session.delete(item)
    try:
        db.session.commit()
        flash('Task deleted.', 'success')
    except Exception:
        db.session.rollback()
        flash('Could not delete task. Please try again.', 'danger')
    return redirect(url_for('checklist.checklist', wedding_id=wedding_id))


# ── Progress JSON (for AJAX calls from overview) ──────────────────────
@checklist_bp.route('/wedding/<int:wedding_id>/checklist/progress')
@login_required
def checklist_progress(wedding_id):
    get_wedding_or_403(wedding_id)   # ownership check only
    items = ChecklistItem.query.filter_by(wedding_id=wedding_id).all()
    total = len(items)
    done  = sum(1 for i in items if i.is_completed)

    by_cat = {}
    for cat in CHECKLIST_CATEGORIES:
        cat_items = [i for i in items if i.category == cat]
        cat_done  = sum(1 for i in cat_items if i.is_completed)
        if cat_items:
            by_cat[cat] = {
                'done':  cat_done,
                'total': len(cat_items),
                'pct':   round(cat_done / len(cat_items) * 100),
            }

    return jsonify({
        'total':       total,
        'done':        done,
        'pct':         round(done / total * 100) if total else 0,
        'by_category': by_cat,
    })
