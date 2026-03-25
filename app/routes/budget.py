from datetime import datetime, timezone
from datetime import date as date_type

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required

from app import db
from app.models import BudgetCategory, Expense
from app.routes.utils import get_budget_category_or_403, get_expense_or_403, get_wedding_or_403

budget_bp = Blueprint('budget', __name__)


def _utcnow():
    return datetime.now(timezone.utc)


def _budget_totals(wedding):
    """Return (total_estimated, total_actual_paid, total_allocated) for a wedding."""
    cats = wedding.budget_categories
    total_estimated    = sum(e.estimated_cost or 0 for cat in cats for e in cat.expenses)
    total_actual_paid  = sum(e.actual_cost or 0 for cat in cats for e in cat.expenses if e.is_paid)
    total_actual_all   = sum(e.actual_cost or 0 for cat in cats for e in cat.expenses)
    total_allocated    = sum(cat.allocated_amount or 0 for cat in cats)
    return total_estimated, total_actual_paid, total_actual_all, total_allocated


# ── Main budget page ──────────────────────────────────────────────────
@budget_bp.route('/wedding/<int:wedding_id>/budget')
@login_required
def budget(wedding_id):
    wedding    = get_wedding_or_403(wedding_id)
    categories = (BudgetCategory.query
                  .filter_by(wedding_id=wedding_id)
                  .order_by(BudgetCategory.created_at)
                  .all())

    total_estimated, total_actual_paid, total_actual_all, total_allocated = _budget_totals(wedding)
    total_budget = wedding.total_budget or 0
    remaining    = total_budget - total_actual_paid

    # Upcoming payments: unpaid expenses with a due_date, sorted soonest first
    upcoming = (Expense.query
                .filter_by(wedding_id=wedding_id, is_paid=False)
                .filter(Expense.due_date.isnot(None))
                .order_by(Expense.due_date)
                .all())

    # Chart.js data
    chart_labels    = [c.name             for c in categories]
    chart_colors    = [c.color            for c in categories]
    chart_allocated = [c.allocated_amount or 0 for c in categories]
    chart_estimated = [sum(e.estimated_cost or 0 for e in c.expenses) for c in categories]
    chart_actual    = [sum(e.actual_cost   or 0 for e in c.expenses if e.is_paid) for c in categories]

    return render_template(
        'wedding/budget.html',
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
    )


# ── Set total budget (JSON) ───────────────────────────────────────────
@budget_bp.route('/wedding/<int:wedding_id>/budget/set-total', methods=['POST'])
@login_required
def set_total(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    try:
        if request.is_json:
            amount = float(request.json.get('amount', 0) or 0)
        else:
            amount = float(request.form.get('amount', 0) or 0)
        amount = max(0, amount)
    except (ValueError, TypeError):
        return jsonify({'ok': False, 'error': 'Invalid amount'}), 400

    wedding.total_budget = amount
    try:
        db.session.commit()
        _, total_actual_paid, _, _ = _budget_totals(wedding)
        remaining = amount - total_actual_paid
        return jsonify({
            'ok': True,
            'total_budget': amount,
            'remaining': remaining,
            'pct': round(total_actual_paid / amount * 100) if amount else 0,
        })
    except Exception:
        db.session.rollback()
        return jsonify({'ok': False, 'error': 'DB error'}), 500


# ── Add category ──────────────────────────────────────────────────────
@budget_bp.route('/wedding/<int:wedding_id>/budget/category/add', methods=['POST'])
@login_required
def add_category(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    name   = request.form.get('name', '').strip()
    color  = request.form.get('color', '#c9687a').strip()
    try:
        allocated = float(request.form.get('allocated_amount', 0) or 0)
    except ValueError:
        allocated = 0

    if not name:
        flash('Category name is required.', 'danger')
        return redirect(url_for('budget.budget', wedding_id=wedding_id))

    cat = BudgetCategory(wedding_id=wedding_id, name=name,
                         allocated_amount=allocated, color=color)
    db.session.add(cat)
    try:
        db.session.commit()
        flash(f'Category "{name}" added.', 'success')
    except Exception:
        db.session.rollback()
        flash('Could not add category.', 'danger')
    return redirect(url_for('budget.budget', wedding_id=wedding_id))


# ── Edit category ─────────────────────────────────────────────────────
@budget_bp.route('/budget/category/<int:cat_id>/edit', methods=['POST'])
@login_required
def edit_category(cat_id):
    cat  = get_budget_category_or_403(cat_id)
    name = request.form.get('name', '').strip()
    try:
        allocated = float(request.form.get('allocated_amount', cat.allocated_amount) or 0)
    except ValueError:
        allocated = cat.allocated_amount
    color = request.form.get('color', cat.color).strip()

    if not name:
        flash('Category name is required.', 'danger')
        return redirect(url_for('budget.budget', wedding_id=cat.wedding_id))

    cat.name             = name
    cat.allocated_amount = allocated
    cat.color            = color
    try:
        db.session.commit()
        flash('Category updated.', 'success')
    except Exception:
        db.session.rollback()
        flash('Could not update category.', 'danger')
    return redirect(url_for('budget.budget', wedding_id=cat.wedding_id))


# ── Delete category ───────────────────────────────────────────────────
@budget_bp.route('/budget/category/<int:cat_id>/delete', methods=['POST'])
@login_required
def delete_category(cat_id):
    cat        = get_budget_category_or_403(cat_id)
    wedding_id = cat.wedding_id
    db.session.delete(cat)
    try:
        db.session.commit()
        flash('Category and all its expenses deleted.', 'success')
    except Exception:
        db.session.rollback()
        flash('Could not delete category.', 'danger')
    return redirect(url_for('budget.budget', wedding_id=wedding_id))


# ── Add expense ───────────────────────────────────────────────────────
@budget_bp.route('/wedding/<int:wedding_id>/budget/expense/add', methods=['POST'])
@login_required
def add_expense(wedding_id):
    wedding     = get_wedding_or_403(wedding_id)
    title       = request.form.get('title', '').strip()
    cat_id_raw  = request.form.get('category_id', '').strip()
    notes       = request.form.get('notes', '').strip() or None
    anchor      = request.form.get('anchor', '')

    if not title:
        flash('Expense title is required.', 'danger')
        return redirect(url_for('budget.budget', wedding_id=wedding_id))

    try:
        estimated = float(request.form.get('estimated_cost', 0) or 0)
    except ValueError:
        estimated = 0
    actual_raw = request.form.get('actual_cost', '').strip()
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
    due_raw  = request.form.get('due_date', '').strip()
    if due_raw:
        try:
            due_date = date_type.fromisoformat(due_raw)
        except ValueError:
            pass

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
    except Exception:
        db.session.rollback()
        flash('Could not add expense.', 'danger')

    redir = url_for('budget.budget', wedding_id=wedding_id)
    if anchor:
        redir += '#' + anchor
    return redirect(redir)


# ── Edit expense ──────────────────────────────────────────────────────
@budget_bp.route('/budget/expense/<int:expense_id>/edit', methods=['POST'])
@login_required
def edit_expense(expense_id):
    expense = get_expense_or_403(expense_id)
    title   = request.form.get('title', '').strip()
    if not title:
        flash('Expense title is required.', 'danger')
        return redirect(url_for('budget.budget', wedding_id=expense.wedding_id))

    try:
        expense.estimated_cost = float(request.form.get('estimated_cost', 0) or 0)
    except ValueError:
        pass
    actual_raw = request.form.get('actual_cost', '').strip()
    expense.actual_cost = float(actual_raw) if actual_raw else None

    due_raw = request.form.get('due_date', '').strip()
    expense.due_date = date_type.fromisoformat(due_raw) if due_raw else None

    cat_id_raw = request.form.get('category_id', '').strip()
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
    expense.notes = request.form.get('notes', '').strip() or None

    try:
        db.session.commit()
        flash('Expense updated.', 'success')
    except Exception:
        db.session.rollback()
        flash('Could not update expense.', 'danger')
    return redirect(url_for('budget.budget', wedding_id=expense.wedding_id))


# ── Delete expense ────────────────────────────────────────────────────
@budget_bp.route('/budget/expense/<int:expense_id>/delete', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense    = get_expense_or_403(expense_id)
    wedding_id = expense.wedding_id
    db.session.delete(expense)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash('Could not delete expense.', 'danger')
    return redirect(url_for('budget.budget', wedding_id=wedding_id))


# ── Toggle paid (AJAX) ────────────────────────────────────────────────
@budget_bp.route('/budget/expense/<int:expense_id>/toggle-paid', methods=['POST'])
@login_required
def toggle_paid(expense_id):
    expense = get_expense_or_403(expense_id)
    expense.is_paid  = not expense.is_paid
    expense.paid_date = date_type.today() if expense.is_paid else None
    try:
        db.session.commit()
        _, total_actual_paid, total_actual_all, _ = _budget_totals(expense.wedding)
        total_budget = expense.wedding.total_budget or 0
        return jsonify({
            'ok':              True,
            'is_paid':         expense.is_paid,
            'paid_date':       expense.paid_date.isoformat() if expense.paid_date else None,
            'total_actual_paid': total_actual_paid,
            'total_actual_all':  total_actual_all,
            'remaining':       total_budget - total_actual_paid,
            'pct':             round(total_actual_paid / total_budget * 100) if total_budget else 0,
        })
    except Exception:
        db.session.rollback()
        return jsonify({'ok': False}), 500


# ── Budget summary JSON (for overview AJAX) ───────────────────────────
@budget_bp.route('/wedding/<int:wedding_id>/budget/summary')
@login_required
def budget_summary(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    total_estimated, total_actual_paid, total_actual_all, total_allocated = _budget_totals(wedding)
    total_budget = wedding.total_budget or 0
    by_cat = {}
    for cat in wedding.budget_categories:
        est  = sum(e.estimated_cost or 0 for e in cat.expenses)
        paid = sum(e.actual_cost or 0 for e in cat.expenses if e.is_paid)
        by_cat[cat.name] = {
            'allocated': cat.allocated_amount,
            'estimated': est,
            'actual':    paid,
            'color':     cat.color,
        }
    return jsonify({
        'total_budget':      total_budget,
        'total_estimated':   total_estimated,
        'total_actual_paid': total_actual_paid,
        'remaining':         total_budget - total_actual_paid,
        'pct':               round(total_actual_paid / total_budget * 100) if total_budget else 0,
        'by_category':       by_cat,
    })
