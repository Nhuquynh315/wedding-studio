"""Default budget category generation for new weddings."""

from app import db
from app.models import BudgetCategory

# (name, percentage_of_total, color)
_DEFAULT_CATEGORIES = [
    ("Venue", 0.30, "#c9687a"),
    ("Catering", 0.35, "#e8a87c"),
    ("Photography", 0.10, "#7cb8e8"),
    ("Flowers", 0.08, "#a8d8a8"),
    ("Music", 0.05, "#d4a8d8"),
    ("Attire", 0.07, "#f0d4a8"),
    ("Stationery", 0.02, "#a8c8d8"),
    ("Transport", 0.03, "#d8c8a8"),
]
_DEFAULT_TOTAL_BUDGET = 20_000.0

assert abs(sum(pct for _, pct, _ in _DEFAULT_CATEGORIES) - 1.0) < 0.001


def create_default_budget(wedding_id, total_budget=None):
    """Seed default budget categories for a new wedding.

    Caller is responsible for db.session.commit().
    """
    total = float(total_budget) if total_budget else _DEFAULT_TOTAL_BUDGET
    categories = [
        BudgetCategory(
            wedding_id=wedding_id,
            name=name,
            allocated_amount=round(total * pct, 2),
            color=color,
        )
        for name, pct, color in _DEFAULT_CATEGORIES
    ]
    db.session.add_all(categories)


def scale_existing_categories(wedding_id, old_total, new_total):
    """Scale every BudgetCategory's allocated_amount by new_total / old_total.

    No-op if old_total is 0 or None (nothing to scale from).
    """
    if not old_total or old_total <= 0:
        return
    if not new_total or new_total <= 0:
        return
    ratio = new_total / old_total
    categories = BudgetCategory.query.filter_by(wedding_id=wedding_id).all()
    for c in categories:
        if c.allocated_amount:
            c.allocated_amount = round(c.allocated_amount * ratio, 2)
