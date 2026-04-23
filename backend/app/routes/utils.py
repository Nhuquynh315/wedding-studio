from flask import abort
from flask_login import current_user

from app.models import BudgetCategory, ChecklistItem, Expense, Guest, Vendor, Wedding


def get_wedding_or_403(wedding_id):
    """Fetch a wedding by ID and abort 403 if it doesn't belong to the current user."""
    wedding = Wedding.query.get_or_404(wedding_id)
    if wedding.user_id != current_user.id:
        abort(403)
    return wedding


def get_guest_or_403(guest_id):
    """Fetch a guest by ID and abort 403 if its wedding doesn't belong to the current user."""
    guest = Guest.query.get_or_404(guest_id)
    if guest.wedding_id is None or guest.wedding.user_id != current_user.id:
        abort(403)
    return guest


def get_budget_category_or_403(category_id):
    """Fetch a budget category and abort 403 if its wedding doesn't belong to the current user."""
    cat = BudgetCategory.query.get_or_404(category_id)
    if cat.wedding.user_id != current_user.id:
        abort(403)
    return cat


def get_expense_or_403(expense_id):
    """Fetch an expense and abort 403 if its wedding doesn't belong to the current user."""
    expense = Expense.query.get_or_404(expense_id)
    if expense.wedding.user_id != current_user.id:
        abort(403)
    return expense


def get_checklist_item_or_403(item_id):
    """Fetch a checklist item and abort 403 if its wedding doesn't belong to the current user."""
    item = ChecklistItem.query.get_or_404(item_id)
    if item.wedding.user_id != current_user.id:
        abort(403)
    return item


def get_vendor_or_403(vendor_id):
    """Fetch a vendor and abort 403 if its wedding doesn't belong to the current user."""
    vendor = Vendor.query.get_or_404(vendor_id)
    if vendor.wedding.user_id != current_user.id:
        abort(403)
    return vendor


def get_table_or_403(table_id):
    """Fetch a WeddingTable and abort 403 if its wedding doesn't belong to the current user."""
    from app.models import WeddingTable
    table = WeddingTable.query.get_or_404(table_id)
    if table.wedding.user_id != current_user.id:
        abort(403)
    return table
