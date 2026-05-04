from typing import Annotated

import pytest
from fastapi import APIRouter, Depends

from api.core.deps import require_wedding_access
from api.main import app as main_app


def _register_and_login(client, email="alice@example.com", password="testpass1234"):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return login.json()["access_token"]


def _create_wedding(db_session, user_id, partner1="Alice", partner2="Bob"):
    from datetime import date

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


def _user_id_from_email(db_session, email):
    from app.models import User

    return db_session.query(User).filter(User.email == email).first().id


_test_router = APIRouter()


@_test_router.get("/test/weddings/{wedding_id}")
def _test_endpoint(wedding: Annotated[object, Depends(require_wedding_access)]):
    return {"wedding_id": wedding.id, "partner1": wedding.partner1_name}


@pytest.fixture(autouse=True)
def _attach_test_router():
    main_app.include_router(_test_router)
    yield
    main_app.routes[:] = [
        r for r in main_app.routes if getattr(r, "path", None) != "/test/weddings/{wedding_id}"
    ]


def test_owner_can_access_their_wedding(client, db_session):
    token = _register_and_login(client)
    user_id = _user_id_from_email(db_session, "alice@example.com")
    wedding = _create_wedding(db_session, user_id)

    resp = client.get(
        f"/test/weddings/{wedding.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["wedding_id"] == wedding.id


def test_other_user_cannot_access_wedding(client, db_session):
    """Critical security test: a user accessing someone else's
    wedding gets 404, not 403 (we hide existence)."""
    _register_and_login(client, "alice@example.com", "testpass1234")
    alice_id = _user_id_from_email(db_session, "alice@example.com")
    alice_wedding = _create_wedding(db_session, alice_id)

    bob_token = _register_and_login(client, "bob@example.com", "testpass5678")

    resp = client.get(
        f"/test/weddings/{alice_wedding.id}",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert resp.status_code == 404


def test_nonexistent_wedding_returns_404(client):
    token = _register_and_login(client)
    resp = client.get(
        "/test/weddings/99999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


def test_unauthenticated_request_returns_401(client):
    """No auth token at all means 401 from get_current_user, not
    404 from require_wedding_access."""
    resp = client.get("/test/weddings/1")
    assert resp.status_code == 401
