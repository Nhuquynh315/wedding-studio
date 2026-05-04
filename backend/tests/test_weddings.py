_VALID_WEDDING = {
    "partner1_name": "Alice",
    "partner2_name": "Bob",
    "wedding_date": "2026-06-15",
    "location": "Adelaide, SA",
    "venue_name": "Magill Estate",
    "style": "modern",
    "primary_color": "#c9687a",
    "secondary_color": "#faf8f5",
}


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_create_wedding(client, register_and_login):
    token = register_and_login(client)
    resp = client.post(
        "/api/v1/weddings",
        json=_VALID_WEDDING,
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["partner1_name"] == "Alice"
    assert data["wedding_date"] == "2026-06-15"
    assert data["user_id"] is not None
    assert "id" in data


def test_create_wedding_requires_auth(client):
    resp = client.post("/api/v1/weddings", json=_VALID_WEDDING)
    assert resp.status_code == 401


def test_create_wedding_validates_required_fields(client, register_and_login):
    token = register_and_login(client)
    resp = client.post(
        "/api/v1/weddings",
        json={"partner1_name": "Alice"},  # missing required fields
        headers=_auth_headers(token),
    )
    assert resp.status_code == 422


def test_list_weddings_returns_only_owned(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    alice_token = register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    create_wedding(db_session, alice_id, partner1="Alice")
    create_wedding(db_session, alice_id, partner1="Alice2")

    bob_token = register_and_login(client, "bob@example.com")
    bob_id = user_id_from_email(db_session, "bob@example.com")
    create_wedding(db_session, bob_id, partner1="Bob")

    resp = client.get("/api/v1/weddings", headers=_auth_headers(alice_token))
    assert resp.status_code == 200
    weddings = resp.json()
    assert len(weddings) == 2
    assert all(w["user_id"] == alice_id for w in weddings)

    resp = client.get("/api/v1/weddings", headers=_auth_headers(bob_token))
    assert len(resp.json()) == 1


def test_get_wedding_returns_owned(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    resp = client.get(
        f"/api/v1/weddings/{wedding.id}",
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == wedding.id


def test_get_other_users_wedding_returns_404(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_wedding = create_wedding(db_session, alice_id)

    bob_token = register_and_login(client, "bob@example.com")
    resp = client.get(
        f"/api/v1/weddings/{alice_wedding.id}",
        headers=_auth_headers(bob_token),
    )
    assert resp.status_code == 404


def test_patch_wedding_updates_only_provided_fields(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id, partner1="Original")
    original_partner2 = wedding.partner2_name

    resp = client.patch(
        f"/api/v1/weddings/{wedding.id}",
        json={"partner1_name": "Updated"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["partner1_name"] == "Updated"
    assert data["partner2_name"] == original_partner2


def test_patch_wedding_validates_field_constraints(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    resp = client.patch(
        f"/api/v1/weddings/{wedding.id}",
        json={"partner1_name": ""},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 422


def test_delete_wedding(client, register_and_login, db_session, create_wedding, user_id_from_email):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    resp = client.delete(
        f"/api/v1/weddings/{wedding.id}",
        headers=_auth_headers(token),
    )
    assert resp.status_code == 204

    resp = client.get(
        f"/api/v1/weddings/{wedding.id}",
        headers=_auth_headers(token),
    )
    assert resp.status_code == 404


def test_delete_other_users_wedding_returns_404(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_wedding = create_wedding(db_session, alice_id)

    bob_token = register_and_login(client, "bob@example.com")
    resp = client.delete(
        f"/api/v1/weddings/{alice_wedding.id}",
        headers=_auth_headers(bob_token),
    )
    assert resp.status_code == 404

    from app.models import Wedding

    still_there = db_session.query(Wedding).filter(Wedding.id == alice_wedding.id).first()
    assert still_there is not None
