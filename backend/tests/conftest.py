import os
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from api.core.db import get_db
from api.main import app
from app.models import Base

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://localhost:5432/wedding_studio_test",
)


@pytest.fixture(scope="session")
def db_engine():
    """One engine for the whole test session. Schema created once."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """
    Each test runs inside a transaction that is rolled back at the end.
    Uses SQLAlchemy's "join an external transaction" recipe so that
    session.commit() inside the code under test doesn't actually commit.
    """
    connection = db_engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection, class_=Session, expire_on_commit=False)
    session = SessionLocal()

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """FastAPI test client wired to the transaction-bound test session."""

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
def create_table():
    """Factory: insert a WeddingTable row directly into the test DB."""

    def _inner(db_session, wedding_id, table_number=1, capacity=8, **kwargs):
        from app.models import WeddingTable

        table = WeddingTable(
            wedding_id=wedding_id,
            table_number=table_number,
            capacity=capacity,
            **kwargs,
        )
        db_session.add(table)
        db_session.commit()
        db_session.refresh(table)
        return table

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
def create_design():
    """Factory: insert a Design row directly into the test DB."""

    def _inner(
        db_session, wedding_id, *, html_content="{}", design_type="invitation", created_at=None
    ):
        from app.models import Design

        design = Design(
            wedding_id=wedding_id,
            design_type=design_type,
            html_content=html_content,
        )
        if created_at is not None:
            design.created_at = created_at
        db_session.add(design)
        db_session.commit()
        db_session.refresh(design)
        return design

    return _inner


@pytest.fixture
def user_id_from_email():
    """Factory: look up a User's id by email in the test DB."""

    def _inner(db_session, email):
        from app.models import User

        return db_session.query(User).filter(User.email == email).first().id

    return _inner
