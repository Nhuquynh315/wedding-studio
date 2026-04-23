"""Default budget category generation for new weddings."""

from app import db
from app.models import BudgetCategory

# (name, allocated_amount, color)  — based on a $20,000 reference budget
_DEFAULT_CATEGORIES = [
    ("Venue", 6000, "#c9687a"),
    ("Catering", 7000, "#e8a87c"),
    ("Photography", 2000, "#7cb8e8"),
    ("Flowers", 1600, "#a8d8a8"),
    ("Music", 1000, "#d4a8d8"),
    ("Attire", 1400, "#f0d4a8"),
    ("Stationery", 400, "#a8c8d8"),
    ("Transport", 600, "#d8c8a8"),
]


def create_default_budget(wedding_id):
    """Seed default budget categories for a new wedding.

    Caller is responsible for db.session.commit().
    """
    categories = [
        BudgetCategory(
            wedding_id=wedding_id,
            name=name,
            allocated_amount=amount,
            color=color,
        )
        for name, amount, color in _DEFAULT_CATEGORIES
    ]
    db.session.add_all(categories)
