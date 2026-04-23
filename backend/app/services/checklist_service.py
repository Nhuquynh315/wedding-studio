"""Default checklist generation for new weddings."""
from datetime import timedelta

from app import db
from app.models import ChecklistItem

# (title, category, days_before_wedding, priority)
_DEFAULT_TASKS = [
    # 14+ months before
    ('Book venue',                      'Venue',       425, 'high'),
    ('Set overall budget',              'Other',       420, 'high'),
    ('Create initial guest list',       'Other',       400, 'high'),
    ('Start wedding dress shopping',    'Attire',      390, 'high'),
    ('Research photographers',          'Photography', 380, 'medium'),
    # 9–12 months before
    ('Book photographer',               'Photography', 330, 'high'),
    ('Book caterer',                    'Catering',    300, 'high'),
    ('Book florist',                    'Flowers',     300, 'high'),
    ('Send save-the-dates',             'Stationery',  300, 'high'),
    ('Plan honeymoon destination',      'Honeymoon',   270, 'medium'),
    ('Book honeymoon travel',           'Honeymoon',   240, 'high'),
    # 6–9 months before
    ('Order wedding dress',             'Attire',      240, 'high'),
    ('Book hair and makeup artist',     'Attire',      210, 'medium'),
    ('Book music / DJ',                 'Music',       210, 'high'),
    ('Plan ceremony details',           'Other',       180, 'medium'),
    ('Register for gifts',              'Other',       180, 'medium'),
    # 4–6 months before
    ('Send invitations',                'Stationery',  150, 'high'),
    ('Plan rehearsal dinner',           'Catering',    150, 'medium'),
    ('Book accommodation for guests',   'Transport',   150, 'medium'),
    ('Order wedding cake',              'Catering',    120, 'high'),
    # 2–4 months before
    ('Confirm all vendors',             'Other',        90, 'high'),
    ('First dress fitting',             'Attire',       90, 'high'),
    ('Create seating chart',            'Other',        60, 'medium'),
    ('Write wedding vows',              'Other',        60, 'medium'),
    ('Finalise honeymoon details',      'Honeymoon',    60, 'low'),
    # 1–2 months before
    ('Final headcount to caterer',      'Catering',     42, 'high'),
    ('Confirm ceremony timeline',       'Other',        30, 'high'),
    ('Final dress fitting and pickup',  'Attire',       30, 'high'),
    ('Prepare vendor payments',         'Other',        30, 'high'),
    # Week of
    ('Final venue walkthrough',         'Venue',         7, 'high'),
    ('Prepare wedding day emergency kit','Other',         7, 'medium'),
    ('Deliver items to venue',          'Venue',         3, 'medium'),
    ('Charge all devices for photos',   'Photography',   2, 'medium'),
    # Day before / day of
    ('Rehearsal dinner',                'Catering',      1, 'high'),
    ('Confirm all transport',           'Transport',     1, 'high'),
    ('Rest and relax',                  'Other',         1, 'low'),
]


def create_default_checklist(wedding_id, wedding_date):
    """Populate a new wedding with the default planning checklist.

    Due dates are calculated relative to the wedding_date.
    If wedding_date is None all due dates are left as None.
    """
    items = []
    for title, category, days_before, priority in _DEFAULT_TASKS:
        due = (wedding_date - timedelta(days=days_before)) if wedding_date else None
        items.append(ChecklistItem(
            wedding_id=wedding_id,
            title=title,
            category=category,
            due_date=due,
            priority=priority,
        ))
    db.session.add_all(items)
    # Caller is responsible for db.session.commit()
