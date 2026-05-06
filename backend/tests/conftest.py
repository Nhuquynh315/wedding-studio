from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.core.db import get_db
from api.main import app


@pytest.fixture
def db_engine():
    """In-memory SQLite engine with all tables created. Fresh per test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    from app import create_app

    _flask_app = create_app()
    with _flask_app.app_context():
        from app import db as _db

        _db.metadata.create_all(bind=engine)

    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """A session that gets closed after each test."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """FastAPI test client wired to the in-memory test DB."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


# ── Shared test helpers (factory fixtures) ────────────────────────────────────


@pytest.fixture
def register_and_login():
    """Factory: register a user and return their access token."""

    def _inner(client, email="alice@example.com", password="testpass1234"):
        client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Test User"},
        )
        login = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        return login.json()["access_token"]

    return _inner


@pytest.fixture
def create_wedding():
    """Factory: insert a Wedding row directly into the test DB."""

    def _inner(db_session, user_id, partner1="Alice", partner2="Bob"):
        from app.models import Wedding

        wedding = Wedding(
            user_id=user_id,
            partner1_name=partner1,
            partner2_name=partner2,
            wedding_date=date(2027, 6, 1),
            location="Test City",
            venue_name="Test Venue",
            style="modern",
            primary_color="#ffffff",
            secondary_color="#000000",
        )
        db_session.add(wedding)
        db_session.commit()
        db_session.refresh(wedding)
        return wedding

    return _inner


@pytest.fixture
def create_guest():
    """Factory: insert a Guest row directly into the test DB."""

    def _inner(db_session, wedding_id, full_name="Charlie", rsvp_status="pending", group_name=None):
        from app.models import Guest

        guest = Guest(
            wedding_id=wedding_id,
            full_name=full_name,
            rsvp_status=rsvp_status,
            group_name=group_name,
        )
        db_session.add(guest)
        db_session.commit()
        db_session.refresh(guest)
        return guest

    return _inner


@pytest.fixture
def create_category():
    """Factory: insert a BudgetCategory row directly into the test DB."""

    def _inner(db_session, wedding_id, name="Test Cat", allocated_amount=1000.0, color=None):
        from app.models import BudgetCategory

        cat = BudgetCategory(
            wedding_id=wedding_id,
            name=name,
            allocated_amount=allocated_amount,
            color=color,
        )
        db_session.add(cat)
        db_session.commit()
        db_session.refresh(cat)
        return cat

    return _inner


@pytest.fixture
def create_expense():
    """Factory: insert an Expense row directly into the test DB."""

    def _inner(
        db_session,
        category_id,
        wedding_id,
        title="Test Expense",
        estimated_cost=100.0,
        actual_cost=None,
        vendor_id=None,
    ):
        from app.models import Expense

        expense = Expense(
            category_id=category_id,
            wedding_id=wedding_id,
            title=title,
            estimated_cost=estimated_cost,
            actual_cost=actual_cost,
            vendor_id=vendor_id,
        )
        db_session.add(expense)
        db_session.commit()
        db_session.refresh(expense)
        return expense

    return _inner


@pytest.fixture
def create_vendor():
    """Factory: insert a Vendor row directly into the test DB."""

    def _inner(db_session, wedding_id, business_name="Test Vendor", **kwargs):
        from app.models import Vendor

        vendor = Vendor(
            wedding_id=wedding_id,
            business_name=business_name,
            status=kwargs.pop("status", "considering"),
            category=kwargs.pop("category", "Other"),
            **kwargs,
        )
        db_session.add(vendor)
        db_session.commit()
        db_session.refresh(vendor)
        return vendor

    return _inner


@pytest.fixture
def create_checklist_item():
    """Factory: insert a ChecklistItem row directly into the test DB."""

    def _inner(db_session, wedding_id, title="Test Task", **kwargs):
        from app.models import ChecklistItem

        item = ChecklistItem(
            wedding_id=wedding_id,
            title=title,
            category=kwargs.pop("category", "Other"),
            priority=kwargs.pop("priority", "medium"),
            is_completed=kwargs.pop("is_completed", False),
            **kwargs,
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        return item

    return _inner


@pytest.fixture
def user_id_from_email():
    """Factory: look up a User's id by email in the test DB."""

    def _inner(db_session, email):
        from app.models import User

        return db_session.query(User).filter(User.email == email).first().id

    return _inner
