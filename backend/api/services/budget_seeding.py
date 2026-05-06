from sqlalchemy.orm import Session

# (name, percentage, color) — same as Flask's _DEFAULT_CATEGORIES
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

assert abs(sum(p for _, p, _ in _DEFAULT_CATEGORIES) - 1.0) < 0.001


def seed_default_categories(
    db: Session,
    wedding_id: int,
    total_budget: float | None = None,
) -> int:
    """Seed the 8 default budget categories for a new wedding.

    Returns the number of categories created.
    """
    from app.models import BudgetCategory

    total = total_budget if total_budget and total_budget > 0 else _DEFAULT_TOTAL_BUDGET

    categories = [
        BudgetCategory(
            wedding_id=wedding_id,
            name=name,
            allocated_amount=round(total * pct, 2),
            color=color,
        )
        for name, pct, color in _DEFAULT_CATEGORIES
    ]
    db.add_all(categories)
    db.flush()
    return len(categories)


def scale_categories(
    db: Session,
    wedding_id: int,
    old_total: float | None,
    new_total: float,
) -> int:
    """Scale every BudgetCategory.allocated_amount by new_total / old_total.

    Falls back to _DEFAULT_TOTAL_BUDGET when old_total is 0 or None —
    handles categories seeded with defaults before a total was set.

    Returns the number of categories scaled.
    """
    from app.models import BudgetCategory

    if not new_total or new_total <= 0:
        return 0

    effective_old = old_total if (old_total and old_total > 0) else _DEFAULT_TOTAL_BUDGET
    ratio = new_total / effective_old

    categories = db.query(BudgetCategory).filter(BudgetCategory.wedding_id == wedding_id).all()

    for cat in categories:
        if cat.allocated_amount:
            cat.allocated_amount = round(cat.allocated_amount * ratio, 2)

    db.flush()
    return len(categories)
