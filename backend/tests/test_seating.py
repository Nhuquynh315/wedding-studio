def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _tables_url(wid):
    return f"/api/v1/weddings/{wid}/tables"


def _table_url(wid, tid):
    return f"/api/v1/weddings/{wid}/tables/{tid}"


def _guest_url(wid, gid):
    return f"/api/v1/weddings/{wid}/guests/{gid}"


# ── CRUD ──────────────────────────────────────────────────────────────────────


def test_list_tables_returns_only_this_wedding(
    client, register_and_login, db_session, create_wedding, create_table, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w1 = create_wedding(db_session, uid)
    w2 = create_wedding(db_session, uid)
    create_table(db_session, w1.id, table_number=1)
    create_table(db_session, w2.id, table_number=1)

    resp = client.get(_tables_url(w1.id), headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["wedding_id"] == w1.id


def test_create_table_201(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.post(
        _tables_url(w.id),
        json={"table_number": 1, "capacity": 10, "table_name": "Head Table"},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["table_number"] == 1
    assert data["capacity"] == 10
    assert data["table_name"] == "Head Table"
    assert data["shape"] == "round"  # default
    assert data["wedding_id"] == w.id
    assert "id" in data


def test_create_table_other_users_wedding_404(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_w = create_wedding(db_session, alice_id)

    bob_token = register_and_login(client, "bob@example.com")
    resp = client.post(
        _tables_url(alice_w.id),
        json={"table_number": 1},
        headers=_auth(bob_token),
    )
    assert resp.status_code == 404


def test_get_table(
    client, register_and_login, db_session, create_wedding, create_table, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    table = create_table(db_session, w.id, table_number=5, table_name="VIP")

    resp = client.get(_table_url(w.id, table.id), headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["table_number"] == 5


def test_get_table_from_wrong_wedding_returns_404(
    client, register_and_login, db_session, create_wedding, create_table, user_id_from_email
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_w = create_wedding(db_session, alice_id)
    alice_table = create_table(db_session, alice_w.id)

    bob_token = register_and_login(client, "bob@example.com")
    bob_id = user_id_from_email(db_session, "bob@example.com")
    bob_w = create_wedding(db_session, bob_id)

    resp = client.get(_table_url(bob_w.id, alice_table.id), headers=_auth(bob_token))
    assert resp.status_code == 404


def test_patch_table_updates_only_provided(
    client, register_and_login, db_session, create_wedding, create_table, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    table = create_table(db_session, w.id, table_number=1, capacity=6)

    resp = client.patch(
        _table_url(w.id, table.id),
        json={"table_name": "Renamed"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["table_name"] == "Renamed"
    assert data["capacity"] == 6  # unchanged


def test_delete_table(
    client, register_and_login, db_session, create_wedding, create_table, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    table = create_table(db_session, w.id)

    resp = client.delete(_table_url(w.id, table.id), headers=_auth(token))
    assert resp.status_code == 204

    resp = client.get(_table_url(w.id, table.id), headers=_auth(token))
    assert resp.status_code == 404


# ── Validation ────────────────────────────────────────────────────────────────


def test_create_table_validates_capacity_lower_bound(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.post(
        _tables_url(w.id),
        json={"table_number": 1, "capacity": 0},
        headers=_auth(token),
    )
    assert resp.status_code == 422


def test_create_table_validates_capacity_upper_bound(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.post(
        _tables_url(w.id),
        json={"table_number": 1, "capacity": 999},
        headers=_auth(token),
    )
    assert resp.status_code == 422


def test_create_table_validates_empty_name(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.post(
        _tables_url(w.id),
        json={"table_number": 1, "table_name": ""},
        headers=_auth(token),
    )
    assert resp.status_code == 422


# ── Guest assignment via PATCH /guests/{id} ───────────────────────────────────


def test_assign_guest_to_table_via_guest_patch(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_table,
    create_guest,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    table = create_table(db_session, w.id)
    guest = create_guest(db_session, w.id, full_name="Alice Smith")

    resp = client.patch(
        _guest_url(w.id, guest.id),
        json={"table_id": table.id},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["table_id"] == table.id


def test_unassign_guest_via_guest_patch_null(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_table,
    create_guest,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    table = create_table(db_session, w.id)
    guest = create_guest(db_session, w.id, full_name="Bob Jones")

    # Assign first
    client.patch(_guest_url(w.id, guest.id), json={"table_id": table.id}, headers=_auth(token))

    # Then unassign
    resp = client.patch(
        _guest_url(w.id, guest.id),
        json={"table_id": None},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["table_id"] is None


def test_overcapacity_assignment_is_allowed(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_table,
    create_guest,
    user_id_from_email,
):
    """API deliberately does not enforce capacity. UI handles the warning.
    Real wedding seating has too many edge cases for strict enforcement."""
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    table = create_table(db_session, w.id, capacity=2)
    g1 = create_guest(db_session, w.id, full_name="Guest 1")
    g2 = create_guest(db_session, w.id, full_name="Guest 2")
    g3 = create_guest(db_session, w.id, full_name="Guest 3")

    for guest in (g1, g2, g3):
        resp = client.patch(
            _guest_url(w.id, guest.id),
            json={"table_id": table.id},
            headers=_auth(token),
        )
        assert resp.status_code == 200, f"assigning {guest.full_name} should succeed"


# ── With-guests view ──────────────────────────────────────────────────────────


def test_with_guests_returns_tables_with_their_assignments(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_table,
    create_guest,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    table_a = create_table(db_session, w.id, table_number=1)
    table_b = create_table(db_session, w.id, table_number=2)
    g1 = create_guest(db_session, w.id, full_name="Guest A1")
    g2 = create_guest(db_session, w.id, full_name="Guest A2")
    g3 = create_guest(db_session, w.id, full_name="Guest B1")
    g4 = create_guest(db_session, w.id, full_name="Unassigned")

    for guest in (g1, g2):
        client.patch(
            _guest_url(w.id, guest.id),
            json={"table_id": table_a.id},
            headers=_auth(token),
        )
    client.patch(
        _guest_url(w.id, g3.id),
        json={"table_id": table_b.id},
        headers=_auth(token),
    )

    resp = client.get(f"{_tables_url(w.id)}/with-guests", headers=_auth(token))
    assert resp.status_code == 200
    tables = resp.json()
    assert len(tables) == 2

    by_id = {t["id"]: t for t in tables}
    assert len(by_id[table_a.id]["guests"]) == 2
    assert len(by_id[table_b.id]["guests"]) == 1

    a_names = {g["full_name"] for g in by_id[table_a.id]["guests"]}
    assert a_names == {"Guest A1", "Guest A2"}
    assert by_id[table_b.id]["guests"][0]["full_name"] == "Guest B1"

    all_guest_ids = {g["id"] for t in tables for g in t["guests"]}
    assert g4.id not in all_guest_ids


def test_with_guests_other_users_wedding_returns_404(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_w = create_wedding(db_session, alice_id)

    bob_token = register_and_login(client, "bob@example.com")
    resp = client.get(f"{_tables_url(alice_w.id)}/with-guests", headers=_auth(bob_token))
    assert resp.status_code == 404


# ── Delete cascade ────────────────────────────────────────────────────────────


def test_delete_table_nullifies_guest_table_id(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_table,
    create_guest,
    user_id_from_email,
):
    """Deleting a table must not delete assigned guests — it must set
    guest.table_id to None (application-level SET NULL)."""
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    table = create_table(db_session, w.id)
    g1 = create_guest(db_session, w.id, full_name="Guest 1")
    g2 = create_guest(db_session, w.id, full_name="Guest 2")

    for guest in (g1, g2):
        client.patch(
            _guest_url(w.id, guest.id),
            json={"table_id": table.id},
            headers=_auth(token),
        )

    resp = client.delete(_table_url(w.id, table.id), headers=_auth(token))
    assert resp.status_code == 204

    for guest in (g1, g2):
        resp = client.get(_guest_url(w.id, guest.id), headers=_auth(token))
        assert resp.status_code == 200, "guest must still exist after table delete"
        assert resp.json()["table_id"] is None, "table_id must be None after table delete"
