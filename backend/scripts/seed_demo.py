"""
Seed a demo account on any database.

Usage (run from backend/):
    SQLALCHEMY_DATABASE_URL="postgresql+psycopg://..." \
    JWT_SECRET_KEY="..." \
    python scripts/seed_demo.py

Idempotent: deletes and recreates demo@weddingstudio.app every run.
Password is intentionally public: DemoPass2026
"""

import os
import sys
from datetime import UTC, date, datetime

# Allow running from backend/ without installing the package
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from api.core.config import settings
from api.core.security import hash_password
from app.models import (
    BudgetCategory,
    ChecklistItem,
    Expense,
    Guest,
    User,
    Vendor,
    Wedding,
    WeddingTable,
)

DEMO_EMAIL = "demo@weddingstudio.app"
DEMO_PASSWORD = "DemoPass2026"

WEDDING_DATE = date(2027, 1, 22)


def utcnow() -> datetime:
    return datetime.now(UTC)


def wipe_demo(session: Session) -> None:
    user = session.query(User).filter_by(email=DEMO_EMAIL).first()
    if user:
        session.delete(user)
        session.commit()
        print("  Wiped existing demo account.")


def seed(session: Session) -> None:
    # ── User ────────────────────────────────────────────────────────
    user = User(
        email=DEMO_EMAIL,
        password_hash=hash_password(DEMO_PASSWORD),
        full_name="Emma & James",
        avatar_color="#c9687a",
        timezone="Australia/Sydney",
        email_notifications=True,
        created_at=utcnow(),
    )
    session.add(user)
    session.flush()

    # ── Wedding ──────────────────────────────────────────────────────
    wedding = Wedding(
        user_id=user.id,
        partner1_name="Emma",
        partner2_name="James",
        wedding_date=WEDDING_DATE,
        location="Sydney, Australia",
        venue_name="Royal Botanic Garden Sydney",
        style="modern",
        primary_color="#c9687a",
        secondary_color="#f5e6c8",
        rsvp_contact="emma.james.wedding@gmail.com",
        total_budget=45000.0,
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    session.add(wedding)
    session.flush()

    # ── Guests ───────────────────────────────────────────────────────
    guests_data = [
        # Family
        ("Margaret Chen", "family@example.com", "0411 111 001", "Family", "chicken", "confirmed"),
        ("Robert Chen", None, "0411 111 002", "Family", "beef", "confirmed"),
        ("Lily Chen", None, "0411 111 003", "Family", "vegetarian", "confirmed"),
        ("David Chen", None, None, "Family", "chicken", "pending"),
        ("Susan Hart", "susan@example.com", "0422 222 001", "Family", "beef", "confirmed"),
        ("Michael Hart", None, "0422 222 002", "Family", "chicken", "confirmed"),
        ("Grace Hart", None, None, "Family", None, "pending"),
        # Friends
        (
            "Sophie Williams",
            "sophie@example.com",
            "0433 333 001",
            "Friends",
            "vegetarian",
            "confirmed",
        ),
        ("Liam Nguyen", None, "0433 333 002", "Friends", "beef", "confirmed"),
        ("Olivia Park", "olivia@example.com", None, "Friends", "chicken", "confirmed"),
        ("Noah Kim", None, None, "Friends", "beef", "pending"),
        ("Ava Thompson", "ava@example.com", "0433 333 005", "Friends", "vegetarian", "declined"),
        ("Ethan Brown", None, None, "Friends", None, "pending"),
        # Work
        ("Rachel Clarke", "rachel@example.com", "0444 444 001", "Work", "chicken", "confirmed"),
        ("Marcus Lee", None, "0444 444 002", "Work", "beef", "confirmed"),
        ("Jessica Wong", "jess@example.com", None, "Work", "vegetarian", "pending"),
        ("Daniel Smith", None, None, "Work", None, "declined"),
        ("Chloe Evans", "chloe@example.com", "0444 444 005", "Work", "chicken", "confirmed"),
    ]

    guests = []
    for full_name, email, phone, group_name, meal, rsvp in guests_data:
        g = Guest(
            wedding_id=wedding.id,
            full_name=full_name,
            email=email,
            phone=phone,
            group_name=group_name,
            meal_preference=meal,
            rsvp_status=rsvp,
            created_at=utcnow(),
        )
        session.add(g)
        guests.append(g)
    session.flush()

    # ── Wedding Tables ───────────────────────────────────────────────
    tables_data = [
        (1, "Bridal Table", 10, "rectangle", 150.0, 100.0),
        (2, "Family", 8, "round", 350.0, 250.0),
        (3, "Friends", 8, "round", 550.0, 250.0),
        (4, "Work", 6, "round", 350.0, 450.0),
    ]
    tables = []
    for number, name, cap, shape, x, y in tables_data:
        t = WeddingTable(
            wedding_id=wedding.id,
            table_number=number,
            table_name=name,
            capacity=cap,
            shape=shape,
            position_x=x,
            position_y=y,
        )
        session.add(t)
        tables.append(t)
    session.flush()

    # Assign confirmed guests to tables
    bridal, family_t, friends_t, work_t = tables
    assignments = {
        bridal: ["Emma & James"],  # symbolic — no guest row for the couple
        family_t: [0, 1, 2, 3, 4, 5],  # indices into guests list
        friends_t: [7, 8, 9, 10, 12],
        work_t: [13, 14, 17],
    }
    for table, guest_indices in assignments.items():
        for idx in guest_indices:
            if not isinstance(idx, int):
                continue
            guests[idx].table_id = table.id
            guests[idx].table_number = table.table_number
    session.flush()

    # ── Budget Categories ────────────────────────────────────────────
    categories_data = [
        ("Venue", 12000.0, "#c9687a"),
        ("Catering", 14000.0, "#e8a87c"),
        ("Photography", 5500.0, "#85c1e9"),
        ("Flowers & Décor", 4000.0, "#a8d5a2"),
        ("Attire", 4500.0, "#bb8fce"),
        ("Music & Entertainment", 2500.0, "#f7dc6f"),
        ("Stationery", 800.0, "#f1948a"),
        ("Transport", 700.0, "#aab7b8"),
    ]
    categories = {}
    for name, amount, color in categories_data:
        c = BudgetCategory(
            wedding_id=wedding.id,
            name=name,
            allocated_amount=amount,
            color=color,
            created_at=utcnow(),
        )
        session.add(c)
        categories[name] = c
    session.flush()

    # ── Vendors ──────────────────────────────────────────────────────
    vendors_data = [
        {
            "category": "Venue",
            "business_name": "Royal Botanic Garden Sydney",
            "contact_name": "Sarah Mitchell",
            "email": "events@rbgsyd.nsw.gov.au",
            "phone": "02 9231 8111",
            "website": "https://www.rbgsyd.nsw.gov.au",
            "quoted_price": 11500.0,
            "deposit_amount": 3000.0,
            "deposit_paid": True,
            "deposit_due_date": date(2026, 8, 1),
            "contracted": True,
            "contract_signed_date": date(2026, 7, 15),
            "status": "booked",
            "rating": 5,
            "notes": "Garden ceremony + terrace reception. Capacity 120.",
        },
        {
            "category": "Catering",
            "business_name": "Harbour Gourmet Co.",
            "contact_name": "Tom Reeves",
            "email": "tom@harbourgourmet.com.au",
            "phone": "02 9555 0200",
            "quoted_price": 13500.0,
            "deposit_amount": 2500.0,
            "deposit_paid": True,
            "deposit_due_date": date(2026, 9, 1),
            "contracted": True,
            "contract_signed_date": date(2026, 8, 20),
            "status": "booked",
            "rating": 4,
            "notes": "3-course menu, canapes, cake cutting included.",
        },
        {
            "category": "Photography",
            "business_name": "Light & Story Photography",
            "contact_name": "Mia Tanaka",
            "email": "mia@lightandstory.com.au",
            "quoted_price": 5200.0,
            "deposit_amount": 1000.0,
            "deposit_paid": True,
            "deposit_due_date": date(2026, 10, 1),
            "contracted": True,
            "status": "booked",
            "rating": 5,
            "notes": "8-hour coverage, 2 photographers, online gallery.",
        },
        {
            "category": "Flowers",
            "business_name": "Petal & Bloom Studio",
            "contact_name": "Claire Dubois",
            "email": "claire@petalandbloom.com.au",
            "quoted_price": 3800.0,
            "deposit_amount": None,
            "deposit_paid": False,
            "contracted": False,
            "status": "considering",
            "rating": 4,
            "notes": "Quote includes bridal bouquet, 6 centrepieces, ceremony arch.",
        },
        {
            "category": "Music",
            "business_name": "Sydney String Quartet",
            "contact_name": "James Brennan",
            "email": "bookings@sydneystrings.com.au",
            "quoted_price": 2200.0,
            "deposit_amount": None,
            "deposit_paid": False,
            "contracted": False,
            "status": "considering",
            "rating": None,
            "notes": "Ceremony + cocktail hour. Need to confirm availability.",
        },
    ]
    vendor_map = {}
    for v_data in vendors_data:
        v = Vendor(
            wedding_id=wedding.id,
            created_at=utcnow(),
            **v_data,
        )
        session.add(v)
        vendor_map[v_data["category"]] = v
    session.flush()

    # ── Expenses ─────────────────────────────────────────────────────
    expenses_data = [
        # Venue
        (
            "Venue hire",
            "Venue",
            "Venue",
            11500.0,
            11500.0,
            True,
            date(2026, 11, 1),
            date(2026, 7, 1),
        ),
        (
            "Venue décor bond",
            "Venue",
            None,
            500.0,
            500.0,
            True,
            date(2026, 10, 15),
            date(2026, 7, 1),
        ),
        # Catering
        (
            "Catering — per head (90 guests)",
            "Catering",
            "Catering",
            13500.0,
            None,
            False,
            date(2027, 1, 15),
            None,
        ),
        ("Welcome drinks", "Catering", None, 800.0, None, False, date(2027, 1, 15), None),
        # Photography
        (
            "Photography package",
            "Photography",
            "Photography",
            5200.0,
            1000.0,
            False,
            date(2027, 1, 22),
            date(2026, 10, 1),
        ),
        # Flowers
        (
            "Flowers & centrepieces",
            "Flowers & Décor",
            "Flowers",
            3800.0,
            None,
            False,
            date(2026, 12, 15),
            None,
        ),
        (
            "Ceremony arch hire",
            "Flowers & Décor",
            None,
            400.0,
            None,
            False,
            date(2026, 12, 15),
            None,
        ),
        # Attire
        ("Wedding gown", "Attire", None, 2800.0, 2800.0, True, date(2026, 9, 1), date(2026, 6, 1)),
        (
            "Suit hire (4 groomsmen)",
            "Attire",
            None,
            1200.0,
            1200.0,
            True,
            date(2026, 11, 1),
            date(2026, 9, 1),
        ),
        # Music
        (
            "String quartet",
            "Music & Entertainment",
            "Music",
            2200.0,
            None,
            False,
            date(2027, 1, 10),
            None,
        ),
        # Stationery
        (
            "Invitations (100)",
            "Stationery",
            None,
            450.0,
            450.0,
            True,
            date(2026, 8, 15),
            date(2026, 7, 15),
        ),
        ("On-the-day stationery", "Stationery", None, 350.0, None, False, date(2026, 12, 1), None),
        # Transport
        ("Bridal car hire", "Transport", None, 700.0, None, False, date(2027, 1, 22), None),
    ]
    for title, cat_name, vendor_cat, estimated, actual, paid, due, paid_date in expenses_data:
        cat = categories.get(cat_name)
        vendor = vendor_map.get(vendor_cat) if vendor_cat else None
        session.add(
            Expense(
                wedding_id=wedding.id,
                category_id=cat.id if cat else None,
                vendor_id=vendor.id if vendor else None,
                title=title,
                estimated_cost=estimated,
                actual_cost=actual,
                is_paid=paid,
                paid_date=paid_date,
                due_date=due,
                created_at=utcnow(),
            )
        )

    # ── Checklist Items ───────────────────────────────────────────────
    done = utcnow()
    checklist_data = [
        # Completed
        ("Book the venue", "Venue", "high", True, date(2026, 6, 1)),
        ("Set the wedding date", "Other", "high", True, date(2026, 5, 15)),
        ("Choose wedding style & colours", "Other", "medium", True, date(2026, 6, 15)),
        ("Book photographer", "Photography", "high", True, date(2026, 8, 1)),
        ("Book catering", "Catering", "high", True, date(2026, 8, 15)),
        ("Order wedding gown", "Attire", "high", True, date(2026, 9, 1)),
        ("Send save-the-dates", "Stationery", "medium", True, date(2026, 8, 1)),
        ("Send invitations", "Stationery", "medium", True, date(2026, 10, 1)),
        # Pending
        ("Book florist", "Flowers", "high", False, date(2026, 11, 1)),
        ("Book string quartet", "Music", "medium", False, date(2026, 11, 15)),
        ("Arrange bridal car", "Transport", "medium", False, date(2026, 12, 1)),
        ("Finalise menu with caterer", "Catering", "high", False, date(2026, 12, 1)),
        ("Collect RSVPs", "Other", "high", False, date(2026, 12, 15)),
        ("Create seating chart", "Other", "high", False, date(2027, 1, 5)),
        ("Confirm ceremony details with officiant", "Other", "high", False, date(2026, 12, 20)),
        ("Book hair & makeup", "Attire", "medium", False, date(2026, 11, 30)),
        ("Order wedding cake", "Catering", "medium", False, date(2026, 11, 1)),
        ("Plan honeymoon", "Honeymoon", "low", False, date(2026, 12, 31)),
        ("Write vows", "Other", "high", False, date(2027, 1, 15)),
        ("Final dress fitting", "Attire", "high", False, date(2027, 1, 10)),
    ]
    for title, category, priority, completed, due in checklist_data:
        session.add(
            ChecklistItem(
                wedding_id=wedding.id,
                title=title,
                category=category,
                priority=priority,
                is_completed=completed,
                completed_at=done if completed else None,
                due_date=due,
                created_at=utcnow(),
            )
        )

    session.commit()
    print(f"  Created user:     {DEMO_EMAIL} / {DEMO_PASSWORD}")
    print(f"  Wedding:          {wedding.partner1_name} & {wedding.partner2_name}, {WEDDING_DATE}")
    print(f"  Guests:           {len(guests_data)}")
    print(f"  Tables:           {len(tables_data)}")
    print(f"  Budget categories:{len(categories_data)}")
    print(f"  Vendors:          {len(vendors_data)}")
    print(f"  Expenses:         {len(expenses_data)}")
    print(f"  Checklist items:  {len(checklist_data)}")


def main() -> None:
    print("Connecting...")
    engine = create_engine(settings.database_url)
    with Session(engine) as session:
        print("Wiping existing demo account (if any)...")
        wipe_demo(session)
        print("Seeding demo data...")
        seed(session)
    print("\nDone. Demo account ready.")
    print("  URL:      https://wedding-studio-one.vercel.app")
    print(f"  Email:    {DEMO_EMAIL}")
    print(f"  Password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
