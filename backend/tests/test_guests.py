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
    data = resp.json()
    assert "items" in data
    assert "next_cursor" in data
    assert "limit" in data
    names = [g["full_name"] for g in data["items"]]
    assert len(names) == 2
    assert "Other Wedding Guest" not in names
    assert data["next_cursor"] is None


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


# ── Pagination ────────────────────────────────────────────────────────────────


def test_list_guests_paginates(
    client, register_and_login, db_session, create_wedding, create_guest, user_id_from_email
):
    """With limit=2 and 5 guests, we should get 2 pages of 2 + 1 page of 1."""
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)
    for i in range(5):
        create_guest(db_session, wedding.id, full_name=f"Guest {i}")

    # Page 1
    resp = client.get(f"{_guests_url(wedding.id)}?limit=2", headers=_auth_headers(token))
    assert resp.status_code == 200
    page1 = resp.json()
    assert len(page1["items"]) == 2
    assert page1["next_cursor"] is not None
    assert [g["full_name"] for g in page1["items"]] == ["Guest 0", "Guest 1"]

    # Page 2
    resp = client.get(
        f"{_guests_url(wedding.id)}?limit=2&cursor={page1['next_cursor']}",
        headers=_auth_headers(token),
    )
    page2 = resp.json()
    assert len(page2["items"]) == 2
    assert page2["next_cursor"] is not None
    assert [g["full_name"] for g in page2["items"]] == ["Guest 2", "Guest 3"]

    # Page 3 (last)
    resp = client.get(
        f"{_guests_url(wedding.id)}?limit=2&cursor={page2['next_cursor']}",
        headers=_auth_headers(token),
    )
    page3 = resp.json()
    assert len(page3["items"]) == 1
    assert page3["next_cursor"] is None
    assert [g["full_name"] for g in page3["items"]] == ["Guest 4"]


def test_list_guests_default_limit_50(
    client, register_and_login, db_session, create_wedding, create_guest, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)
    for i in range(60):
        create_guest(db_session, wedding.id, full_name=f"G{i}")

    resp = client.get(_guests_url(wedding.id), headers=_auth_headers(token))
    data = resp.json()
    assert data["limit"] == 50
    assert len(data["items"]) == 50
    assert data["next_cursor"] is not None


def test_list_guests_limit_max_200(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    resp = client.get(f"{_guests_url(wedding.id)}?limit=300", headers=_auth_headers(token))
    assert resp.status_code == 422


def test_list_guests_invalid_cursor_returns_422(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    resp = client.get(
        f"{_guests_url(wedding.id)}?cursor=this-is-not-base64",
        headers=_auth_headers(token),
    )
    assert resp.status_code == 422


# ── RSVP filter ───────────────────────────────────────────────────────────────


def test_list_guests_filter_by_rsvp(
    client, register_and_login, db_session, create_wedding, create_guest, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)
    create_guest(db_session, wedding.id, full_name="Conf 1", rsvp_status="confirmed")
    create_guest(db_session, wedding.id, full_name="Conf 2", rsvp_status="confirmed")
    create_guest(db_session, wedding.id, full_name="Pending 1", rsvp_status="pending")
    create_guest(db_session, wedding.id, full_name="Declined 1", rsvp_status="declined")

    resp = client.get(f"{_guests_url(wedding.id)}?rsvp=confirmed", headers=_auth_headers(token))
    data = resp.json()
    assert len(data["items"]) == 2
    assert all(g["rsvp_status"] == "confirmed" for g in data["items"])


def test_list_guests_filter_invalid_rsvp_returns_422(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    resp = client.get(f"{_guests_url(wedding.id)}?rsvp=maybe", headers=_auth_headers(token))
    assert resp.status_code == 422


def test_list_guests_filter_and_pagination_combined(
    client, register_and_login, db_session, create_wedding, create_guest, user_id_from_email
):
    """Filter + pagination together: confirmed guests never bleed through."""
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)
    for i in range(5):
        create_guest(db_session, wedding.id, full_name=f"Pending {i}", rsvp_status="pending")
    for i in range(3):
        create_guest(db_session, wedding.id, full_name=f"Conf {i}", rsvp_status="confirmed")

    # First page of pending, limit=2
    resp = client.get(
        f"{_guests_url(wedding.id)}?rsvp=pending&limit=2",
        headers=_auth_headers(token),
    )
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["next_cursor"] is not None
    assert all(g["rsvp_status"] == "pending" for g in data["items"])

    # Second page of pending using cursor
    resp = client.get(
        f"{_guests_url(wedding.id)}?rsvp=pending&limit=2&cursor={data['next_cursor']}",
        headers=_auth_headers(token),
    )
    data = resp.json()
    assert len(data["items"]) >= 1
    assert all(g["rsvp_status"] == "pending" for g in data["items"])
    assert not any(g["rsvp_status"] == "confirmed" for g in data["items"])


# ── Bulk RSVP update ──────────────────────────────────────────────────────────


def _bulk_url(wedding_id: int) -> str:
    return f"/api/v1/weddings/{wedding_id}/guests/bulk-rsvp"


def test_bulk_rsvp_updates_group(
    client, register_and_login, db_session, create_wedding, create_guest, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)
    create_guest(db_session, wedding.id, full_name="Alice Smith", group_name="Smith Family")
    create_guest(db_session, wedding.id, full_name="Bob Smith", group_name="Smith Family")
    create_guest(db_session, wedding.id, full_name="Charlie Doe", group_name="Doe Family")

    resp = client.post(
        _bulk_url(wedding.id),
        json={"rsvp_status": "confirmed", "group_name": "Smith Family"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json() == {"updated_count": 2}

    resp = client.get(f"{_guests_url(wedding.id)}?rsvp=confirmed", headers=_auth_headers(token))
    confirmed = resp.json()["items"]
    assert len(confirmed) == 2
    assert {g["full_name"] for g in confirmed} == {"Alice Smith", "Bob Smith"}


def test_bulk_rsvp_no_group_updates_all(
    client, register_and_login, db_session, create_wedding, create_guest, user_id_from_email
):
    """Without group_name, all guests in the wedding are updated."""
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)
    for i in range(5):
        create_guest(db_session, wedding.id, full_name=f"Guest {i}")

    resp = client.post(
        _bulk_url(wedding.id),
        json={"rsvp_status": "declined"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json() == {"updated_count": 5}


def test_bulk_rsvp_empty_match_returns_zero(
    client, register_and_login, db_session, create_wedding, create_guest, user_id_from_email
):
    """No matching guests is success with updated_count=0, not an error."""
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)
    create_guest(db_session, wedding.id, full_name="Alice")

    resp = client.post(
        _bulk_url(wedding.id),
        json={"rsvp_status": "confirmed", "group_name": "Nonexistent Group"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json() == {"updated_count": 0}


def test_bulk_rsvp_does_not_affect_other_weddings(
    client, register_and_login, db_session, create_wedding, create_guest, user_id_from_email
):
    """Bulk update on wedding 1 must not touch wedding 2's guests."""
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    w1 = create_wedding(db_session, user_id)
    w2 = create_wedding(db_session, user_id)
    create_guest(db_session, w1.id, full_name="W1 Guest", group_name="Family")
    w2_guest = create_guest(db_session, w2.id, full_name="W2 Guest", group_name="Family")

    resp = client.post(
        _bulk_url(w1.id),
        json={"rsvp_status": "confirmed", "group_name": "Family"},
        headers=_auth_headers(token),
    )
    assert resp.json()["updated_count"] == 1

    from app.models import Guest

    db_session.expire_all()
    still_pending = db_session.query(Guest).filter(Guest.id == w2_guest.id).first()
    assert still_pending.rsvp_status == "pending"


def test_bulk_rsvp_other_users_wedding_returns_404(
    client, register_and_login, db_session, create_wedding, create_guest, user_id_from_email
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_wedding = create_wedding(db_session, alice_id)
    create_guest(db_session, alice_wedding.id, full_name="Alice's Guest")

    bob_token = register_and_login(client, "bob@example.com")
    resp = client.post(
        _bulk_url(alice_wedding.id),
        json={"rsvp_status": "confirmed"},
        headers=_auth_headers(bob_token),
    )
    assert resp.status_code == 404


def test_bulk_rsvp_invalid_status_returns_422(
    client, register_and_login, db_session, create_wedding, create_guest, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    resp = client.post(
        _bulk_url(wedding.id),
        json={"rsvp_status": "maybe"},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 422


# ── CSV import ────────────────────────────────────────────────────────────────


def _import_url(wedding_id: int) -> str:
    return f"/api/v1/weddings/{wedding_id}/guests/import"


def _csv_bytes(content: str) -> bytes:
    return content.encode("utf-8")


def test_csv_import_creates_guests(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    csv = "full_name,email,rsvp_status\nAlice,alice@example.com,confirmed\nBob,bob@example.com,pending\n"
    resp = client.post(
        _import_url(wedding.id),
        files={"file": ("guests.csv", _csv_bytes(csv), "text/csv")},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json() == {"imported": 2}

    resp = client.get(_guests_url(wedding.id), headers=_auth_headers(token))
    items = resp.json()["items"]
    assert len(items) == 2
    assert {g["full_name"] for g in items} == {"Alice", "Bob"}


def test_csv_import_minimal_only_full_name(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    """CSV with only the required column works."""
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    csv = "full_name\nAlice\nBob\nCharlie\n"
    resp = client.post(
        _import_url(wedding.id),
        files={"file": ("guests.csv", _csv_bytes(csv), "text/csv")},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json() == {"imported": 3}


def test_csv_import_empty_rsvp_defaults_to_pending(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    csv = "full_name,rsvp_status\nAlice,\nBob,confirmed\n"
    resp = client.post(
        _import_url(wedding.id),
        files={"file": ("guests.csv", _csv_bytes(csv), "text/csv")},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200

    resp = client.get(_guests_url(wedding.id), headers=_auth_headers(token))
    items = {g["full_name"]: g["rsvp_status"] for g in resp.json()["items"]}
    assert items == {"Alice": "pending", "Bob": "confirmed"}


def test_csv_import_unknown_columns_are_ignored(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    """Extra columns shouldn't cause errors."""
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    csv = "full_name,email,future_field,xyz\nAlice,alice@example.com,foo,bar\n"
    resp = client.post(
        _import_url(wedding.id),
        files={"file": ("guests.csv", _csv_bytes(csv), "text/csv")},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json() == {"imported": 1}


def test_csv_import_bom_tolerated(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    """CSVs saved by Excel often have a UTF-8 BOM at the start."""
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    csv_with_bom = b"\xef\xbb\xbf" + b"full_name\nAlice\n"
    resp = client.post(
        _import_url(wedding.id),
        files={"file": ("guests.csv", csv_with_bom, "text/csv")},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json() == {"imported": 1}


def test_csv_import_missing_required_column_returns_400(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    csv = "email,phone\nalice@example.com,+61400111222\n"
    resp = client.post(
        _import_url(wedding.id),
        files={"file": ("guests.csv", _csv_bytes(csv), "text/csv")},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 400
    assert "full_name" in resp.json()["detail"]


def test_csv_import_invalid_email_rejects_entire_upload(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    """All-or-nothing semantics: row 2 is bad, so row 1 is also rejected."""
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    csv = "full_name,email\nAlice,alice@example.com\nBob,not-an-email\n"
    resp = client.post(
        _import_url(wedding.id),
        files={"file": ("guests.csv", _csv_bytes(csv), "text/csv")},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 400

    row_errors = resp.json()["row_errors"]
    assert len(row_errors) == 1
    assert row_errors[0]["row"] == 2
    assert "email" in row_errors[0]["errors"]

    # Verify NEITHER guest was imported
    resp = client.get(_guests_url(wedding.id), headers=_auth_headers(token))
    assert len(resp.json()["items"]) == 0


def test_csv_import_invalid_rsvp_status_rejected(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    csv = "full_name,rsvp_status\nAlice,maybe\n"
    resp = client.post(
        _import_url(wedding.id),
        files={"file": ("guests.csv", _csv_bytes(csv), "text/csv")},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 400
    assert resp.json()["row_errors"][0]["row"] == 1


def test_csv_import_other_users_wedding_returns_404(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_wedding = create_wedding(db_session, alice_id)

    bob_token = register_and_login(client, "bob@example.com")
    csv = "full_name\nIntruder\n"
    resp = client.post(
        _import_url(alice_wedding.id),
        files={"file": ("guests.csv", _csv_bytes(csv), "text/csv")},
        headers=_auth_headers(bob_token),
    )
    assert resp.status_code == 404


def test_csv_import_empty_file_returns_400(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    resp = client.post(
        _import_url(wedding.id),
        files={"file": ("guests.csv", b"", "text/csv")},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 400


def test_csv_import_oversized_file_returns_400(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    """Files over 1 MB should be rejected."""
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    header = "full_name\n"
    row = "A" * 100 + "\n"
    big_csv = header + row * 11000  # ~1.1 MB
    assert len(big_csv) > 1024 * 1024

    resp = client.post(
        _import_url(wedding.id),
        files={"file": ("guests.csv", _csv_bytes(big_csv), "text/csv")},
        headers=_auth_headers(token),
    )
    assert resp.status_code == 400
    assert "too large" in resp.json()["detail"].lower()
