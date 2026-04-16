"""
Cross-feature connection utilities.

All functions use late imports to avoid circular import issues — safe to call
from any route file.
"""
from datetime import datetime, timezone

# Maps vendor category → task title keywords to match against
VENDOR_TO_TASK = {
    'Venue':         ['venue', 'book venue', 'choose venue'],
    'Catering':      ['cater', 'food', 'catering'],
    'Photography':   ['photo', 'photographer'],
    'Videography':   ['video', 'videograph'],
    'Flowers':       ['florist', 'flower', 'floral'],
    'Music':         ['music', 'band', 'dj', 'entertainment'],
    'Hair & Makeup': ['hair', 'makeup', 'beauty'],
    'Transport':     ['transport', 'car', 'limo'],
    'Cake':          ['cake', 'dessert'],
    'Stationery':    ['stationery', 'invitation', 'invite'],
    'Officiant':     ['officiant', 'celebrant', 'ceremony'],
}


def _utcnow():
    return datetime.now(timezone.utc)


def auto_complete_vendor_task(wedding_id, vendor_category):
    """Find the first incomplete checklist task matching the vendor category
    and mark it complete. Returns the task title if found, else None."""
    from app import db
    from app.models import ChecklistItem

    keywords = VENDOR_TO_TASK.get(vendor_category, [])
    if not keywords:
        return None

    items = ChecklistItem.query.filter_by(
        wedding_id=wedding_id,
        is_completed=False,
    ).all()

    for item in items:
        if any(kw in item.title.lower() for kw in keywords):
            item.is_completed = True
            item.completed_at = _utcnow()
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                return None
            return item.title

    return None


def auto_complete_task_by_keyword(wedding_id, keywords):
    """Mark complete all incomplete tasks whose titles match any keyword.
    Returns list of completed task titles."""
    from app import db
    from app.models import ChecklistItem

    items = ChecklistItem.query.filter_by(
        wedding_id=wedding_id,
        is_completed=False,
    ).all()

    completed = []
    for item in items:
        if any(kw in item.title.lower() for kw in keywords):
            item.is_completed = True
            item.completed_at = _utcnow()
            completed.append(item.title)

    if completed:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            return []

    return completed


def check_budget_completion(wedding_id):
    """If total actual spend has reached or exceeded the wedding's total budget,
    auto-complete any 'finalise/confirm/set budget' checklist tasks."""
    from app import db
    from app.models import Wedding, Expense

    wedding = Wedding.query.get(wedding_id)
    if not wedding or not wedding.total_budget:
        return

    total_spent = (
        db.session.query(db.func.sum(Expense.actual_cost))
        .filter(
            Expense.wedding_id == wedding_id,
            Expense.actual_cost.isnot(None),
        )
        .scalar() or 0
    )

    if total_spent >= wedding.total_budget:
        auto_complete_task_by_keyword(
            wedding_id,
            ['finalise budget', 'finalize budget', 'confirm budget', 'set budget'],
        )
