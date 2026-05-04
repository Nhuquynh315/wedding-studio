from typing import Annotated

import pytest
from fastapi import APIRouter, Depends

from api.core.deps import require_wedding_access
from api.main import app as main_app

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


def test_owner_can_access_their_wedding(
    client, db_session, register_and_login, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    resp = client.get(
        f"/test/weddings/{wedding.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["wedding_id"] == wedding.id


def test_other_user_cannot_access_wedding(
    client, db_session, register_and_login, create_wedding, user_id_from_email
):
    """Critical security test: a user accessing someone else's
    wedding gets 404, not 403 (we hide existence)."""
    register_and_login(client, "alice@example.com", "testpass1234")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_wedding = create_wedding(db_session, alice_id)

    bob_token = register_and_login(client, "bob@example.com", "testpass5678")

    resp = client.get(
        f"/test/weddings/{alice_wedding.id}",
        headers={"Authorization": f"Bearer {bob_token}"},
    )
    assert resp.status_code == 404


def test_nonexistent_wedding_returns_404(client, register_and_login):
    token = register_and_login(client)
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
