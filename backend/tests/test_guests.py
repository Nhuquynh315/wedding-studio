def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _guests_url(wedding_id: int) -> str:
    return f"/api/v1/weddings/{wedding_id}/guests"


def _guest_url(wedding_id: int, guest_id: int) -> str:
    return f"/api/v1/weddings/{wedding_id}/guests/{guest_id}"


# ── List ──────────────────────────────────────────────────────────────────────


def test_list_guests_returns_only_this_weddings_guests(
    client, register_and_login, db_session, create_wedding, create_guest, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    w1 = create_wedding(db_session, user_id)
    w2 = create_wedding(db_session, user_id)
    create_guest(db_session, w1.id, full_name="Alice Guest")
    create_guest(db_session, w1.id, full_name="Bob Guest")
    create_guest(db_session, w2.id, full_name="Other Wedding Guest")

    resp = client.get(_guests_url(w1.id), headers=_auth_headers(token))
    assert resp.status_code == 200
    names = [g["full_name"] for g in resp.json()]
    assert len(names) == 2
    assert "Other Wedding Guest" not in names


def test_list_guests_requires_auth(
    client, db_session, create_wedding, register_and_login, user_id_from_email
):
    register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)
    resp = client.get(_guests_url(wedding.id))
    assert resp.status_code == 401


def test_list_guests_other_users_wedding_returns_404(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_wedding = create_wedding(db_session, alice_id)

    bob_token = register_and_login(client, "bob@example.com")
    resp = client.get(_guests_url(alice_wedding.id), headers=_auth_headers(bob_token))
    assert resp.status_code == 404


# ── Create ────────────────────────────────────────────────────────────────────


def test_create_guest(client, register_and_login, db_session, create_wedding, user_id_from_email):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    resp = client.post(
        _guests_url(wedding.id),
        json={"full_name": "Dana Smith", "rsvp_status": "confirmed"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["full_name"] == "Dana Smith"
    assert data["rsvp_status"] == "confirmed"
    assert data["wedding_id"] == wedding.id
    assert "id" in data


def test_create_guest_defaults_rsvp_to_pending(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    resp = client.post(
        _guests_url(wedding.id),
        json={"full_name": "Eve"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 201
    assert resp.json()["rsvp_status"] == "pending"


def test_create_guest_invalid_rsvp_status_returns_422(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    resp = client.post(
        _guests_url(wedding.id),
        json={"full_name": "Eve", "rsvp_status": "maybe"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 422


# ── Get ───────────────────────────────────────────────────────────────────────


def test_get_guest(
    client, register_and_login, db_session, create_wedding, create_guest, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)
    guest = create_guest(db_session, wedding.id, full_name="Frank")

    resp = client.get(_guest_url(wedding.id, guest.id), headers=_auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["id"] == guest.id
    assert resp.json()["full_name"] == "Frank"


def test_get_nonexistent_guest_returns_404(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    resp = client.get(_guest_url(wedding.id, 99999), headers=_auth_headers(token))
    assert resp.status_code == 404


# ── Patch ─────────────────────────────────────────────────────────────────────


def test_patch_guest_updates_rsvp_status(
    client, register_and_login, db_session, create_wedding, create_guest, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)
    guest = create_guest(db_session, wedding.id, full_name="Grace", rsvp_status="pending")

    resp = client.patch(
        _guest_url(wedding.id, guest.id),
        json={"rsvp_status": "confirmed"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["rsvp_status"] == "confirmed"
    assert data["full_name"] == "Grace"


def test_patch_guest_validates_empty_name(
    client, register_and_login, db_session, create_wedding, create_guest, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)
    guest = create_guest(db_session, wedding.id)

    resp = client.patch(
        _guest_url(wedding.id, guest.id),
        json={"full_name": ""},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 422


# ── Delete ────────────────────────────────────────────────────────────────────


def test_delete_guest(
    client, register_and_login, db_session, create_wedding, create_guest, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)
    guest = create_guest(db_session, wedding.id)

    resp = client.delete(_guest_url(wedding.id, guest.id), headers=_auth_headers(token))
    assert resp.status_code == 204

    resp = client.get(_guest_url(wedding.id, guest.id), headers=_auth_headers(token))
    assert resp.status_code == 404


def test_delete_guest_from_other_users_wedding_returns_404(
    client, register_and_login, db_session, create_wedding, create_guest, user_id_from_email
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_wedding = create_wedding(db_session, alice_id)
    guest = create_guest(db_session, alice_wedding.id)

    bob_token = register_and_login(client, "bob@example.com")
    resp = client.delete(_guest_url(alice_wedding.id, guest.id), headers=_auth_headers(bob_token))
    assert resp.status_code == 404

    from app.models import Guest

    still_there = db_session.query(Guest).filter(Guest.id == guest.id).first()
    assert still_there is not None
