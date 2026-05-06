def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _checklist_url(wid):
    return f"/api/v1/weddings/{wid}/checklist"


def _item_url(wid, iid):
    return f"/api/v1/weddings/{wid}/checklist/{iid}"


# ── CRUD ──────────────────────────────────────────────────────────────────────


def test_list_items_returns_only_this_wedding(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_checklist_item,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w1 = create_wedding(db_session, uid)
    w2 = create_wedding(db_session, uid)
    create_checklist_item(db_session, w1.id, title="W1 Task")
    create_checklist_item(db_session, w2.id, title="W2 Task")

    resp = client.get(_checklist_url(w1.id), headers=_auth(token))
    assert resp.status_code == 200
    titles = [i["title"] for i in resp.json()]
    assert "W1 Task" in titles
    assert "W2 Task" not in titles


def test_create_item_201(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.post(
        _checklist_url(w.id),
        json={"title": "Book venue", "category": "Venue", "priority": "high"},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Book venue"
    assert data["category"] == "Venue"
    assert data["priority"] == "high"
    assert data["is_completed"] is False
    assert data["wedding_id"] == w.id
    assert "id" in data


def test_create_item_other_users_wedding_404(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_w = create_wedding(db_session, alice_id)

    bob_token = register_and_login(client, "bob@example.com")
    resp = client.post(
        _checklist_url(alice_w.id),
        json={"title": "Intruder task"},
        headers=_auth(bob_token),
    )
    assert resp.status_code == 404


def test_get_item(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_checklist_item,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    item = create_checklist_item(db_session, w.id, title="Send invites")

    resp = client.get(_item_url(w.id, item.id), headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["title"] == "Send invites"


def test_get_item_from_wrong_wedding_returns_404(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_checklist_item,
    user_id_from_email,
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_w = create_wedding(db_session, alice_id)
    alice_item = create_checklist_item(db_session, alice_w.id)

    bob_token = register_and_login(client, "bob@example.com")
    bob_id = user_id_from_email(db_session, "bob@example.com")
    bob_w = create_wedding(db_session, bob_id)

    resp = client.get(_item_url(bob_w.id, alice_item.id), headers=_auth(bob_token))
    assert resp.status_code == 404


def test_patch_item_updates_only_provided(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_checklist_item,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    item = create_checklist_item(db_session, w.id, title="Original", priority="low")

    resp = client.patch(
        _item_url(w.id, item.id),
        json={"title": "Updated"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Updated"
    assert data["priority"] == "low"  # unchanged


def test_patch_item_can_toggle_completed(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_checklist_item,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    item = create_checklist_item(db_session, w.id, is_completed=False)

    resp = client.patch(
        _item_url(w.id, item.id),
        json={"is_completed": True},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_completed"] is True
    assert data["completed_at"] is not None


def test_delete_item(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_checklist_item,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    item = create_checklist_item(db_session, w.id)

    resp = client.delete(_item_url(w.id, item.id), headers=_auth(token))
    assert resp.status_code == 204

    resp = client.get(_item_url(w.id, item.id), headers=_auth(token))
    assert resp.status_code == 404


# ── Validation ────────────────────────────────────────────────────────────────


def test_create_item_invalid_category_returns_422(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.post(
        _checklist_url(w.id),
        json={"title": "Bad category", "category": "Balloons"},
        headers=_auth(token),
    )
    assert resp.status_code == 422


def test_create_item_invalid_priority_returns_422(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.post(
        _checklist_url(w.id),
        json={"title": "Bad priority", "priority": "urgent"},
        headers=_auth(token),
    )
    assert resp.status_code == 422


def test_create_item_empty_title_returns_422(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.post(
        _checklist_url(w.id),
        json={"title": ""},
        headers=_auth(token),
    )
    assert resp.status_code == 422


# ── Filters ───────────────────────────────────────────────────────────────────


def test_list_items_filter_by_category(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_checklist_item,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    create_checklist_item(db_session, w.id, title="Venue task", category="Venue")
    create_checklist_item(db_session, w.id, title="Catering task", category="Catering")

    resp = client.get(f"{_checklist_url(w.id)}?category=Venue", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["category"] == "Venue"


def test_list_items_filter_by_priority(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_checklist_item,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    create_checklist_item(db_session, w.id, title="High task", priority="high")
    create_checklist_item(db_session, w.id, title="Low task", priority="low")
    create_checklist_item(db_session, w.id, title="Another high", priority="high")

    resp = client.get(f"{_checklist_url(w.id)}?priority=high", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(i["priority"] == "high" for i in data)


def test_list_items_filter_by_completed(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_checklist_item,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    create_checklist_item(db_session, w.id, title="Done", is_completed=True)
    create_checklist_item(db_session, w.id, title="Pending", is_completed=False)

    resp = client.get(f"{_checklist_url(w.id)}?completed=true", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["is_completed"] is True


def test_list_items_combined_filters(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_checklist_item,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    create_checklist_item(
        db_session, w.id, title="Match", category="Catering", priority="high", is_completed=True
    )
    create_checklist_item(
        db_session,
        w.id,
        title="Wrong completed",
        category="Catering",
        priority="high",
        is_completed=False,
    )
    create_checklist_item(
        db_session,
        w.id,
        title="Wrong priority",
        category="Catering",
        priority="low",
        is_completed=True,
    )
    create_checklist_item(
        db_session,
        w.id,
        title="Wrong category",
        category="Venue",
        priority="high",
        is_completed=True,
    )
    create_checklist_item(
        db_session,
        w.id,
        title="Wrong all",
        category="Flowers",
        priority="medium",
        is_completed=False,
    )

    resp = client.get(
        f"{_checklist_url(w.id)}?category=Catering&priority=high&completed=true",
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Match"


# ── Bulk complete ─────────────────────────────────────────────────────────────


def test_bulk_complete_with_category(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_checklist_item,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    create_checklist_item(db_session, w.id, title="Catering 1", category="Catering")
    create_checklist_item(db_session, w.id, title="Catering 2", category="Catering")
    create_checklist_item(db_session, w.id, title="Catering 3", category="Catering")
    create_checklist_item(db_session, w.id, title="Venue 1", category="Venue")

    resp = client.post(
        f"{_checklist_url(w.id)}/bulk-complete",
        json={"completed": True, "category": "Catering"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["updated_count"] == 3

    items = client.get(_checklist_url(w.id), headers=_auth(token)).json()
    catering = [i for i in items if i["category"] == "Catering"]
    venue = [i for i in items if i["category"] == "Venue"]
    assert all(i["is_completed"] for i in catering)
    assert all(not i["is_completed"] for i in venue)


def test_bulk_complete_no_category_updates_all(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_checklist_item,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    create_checklist_item(db_session, w.id, title="T1", category="Venue")
    create_checklist_item(db_session, w.id, title="T2", category="Catering")
    create_checklist_item(db_session, w.id, title="T3", category="Attire")
    create_checklist_item(db_session, w.id, title="T4", category="Music")
    create_checklist_item(db_session, w.id, title="T5", category="Other")

    resp = client.post(
        f"{_checklist_url(w.id)}/bulk-complete",
        json={"completed": True},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["updated_count"] == 5

    items = client.get(_checklist_url(w.id), headers=_auth(token)).json()
    assert all(i["is_completed"] for i in items)


def test_bulk_complete_other_users_wedding_404(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_w = create_wedding(db_session, alice_id)

    bob_token = register_and_login(client, "bob@example.com")
    resp = client.post(
        f"{_checklist_url(alice_w.id)}/bulk-complete",
        json={"completed": True},
        headers=_auth(bob_token),
    )
    assert resp.status_code == 404


def test_bulk_complete_invalid_category_returns_422(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.post(
        f"{_checklist_url(w.id)}/bulk-complete",
        json={"completed": True, "category": "InvalidCategory"},
        headers=_auth(token),
    )
    assert resp.status_code == 422


def test_bulk_complete_does_not_affect_other_weddings(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_checklist_item,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w1 = create_wedding(db_session, uid)
    w2 = create_wedding(db_session, uid)
    create_checklist_item(db_session, w1.id, title="W1 Task")
    create_checklist_item(db_session, w2.id, title="W2 Task")

    resp = client.post(
        f"{_checklist_url(w1.id)}/bulk-complete",
        json={"completed": True},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["updated_count"] == 1

    w2_items = client.get(_checklist_url(w2.id), headers=_auth(token)).json()
    assert all(not i["is_completed"] for i in w2_items)
