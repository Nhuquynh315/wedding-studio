_VALID_WEDDING = {
    "partner1_name": "Alice",
    "partner2_name": "Bob",
    "wedding_date": "2027-06-01",
    "location": "Test City",
    "venue_name": "Test Venue",
    "style": "modern",
    "primary_color": "#ffffff",
    "secondary_color": "#000000",
}


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _cats_url(wid):
    return f"/api/v1/weddings/{wid}/budget/categories"


def _cat_url(wid, cid):
    return f"/api/v1/weddings/{wid}/budget/categories/{cid}"


def _expenses_url(wid):
    return f"/api/v1/weddings/{wid}/budget/expenses"


def _expense_url(wid, eid):
    return f"/api/v1/weddings/{wid}/budget/expenses/{eid}"


def _scale_url(wid):
    return f"/api/v1/weddings/{wid}/budget/scale"


def _summary_url(wid):
    return f"/api/v1/weddings/{wid}/budget/summary"


# ── Categories ────────────────────────────────────────────────────────────────


def test_wedding_create_seeds_default_categories(client, register_and_login):
    token = register_and_login(client)
    resp = client.post("/api/v1/weddings", json=_VALID_WEDDING, headers=_auth(token))
    assert resp.status_code == 201
    wid = resp.json()["id"]

    resp = client.get(_cats_url(wid), headers=_auth(token))
    assert resp.status_code == 200
    cats = resp.json()
    assert len(cats) == 8
    names = {c["name"] for c in cats}
    assert names == {
        "Venue",
        "Catering",
        "Photography",
        "Flowers",
        "Music",
        "Attire",
        "Stationery",
        "Transport",
    }


def test_list_categories_returns_only_this_wedding(
    client, register_and_login, db_session, create_wedding, create_category, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w1 = create_wedding(db_session, uid)
    w2 = create_wedding(db_session, uid)
    create_category(db_session, w1.id, name="W1 Cat")
    create_category(db_session, w2.id, name="W2 Cat")

    resp = client.get(_cats_url(w1.id), headers=_auth(token))
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert "W1 Cat" in names
    assert "W2 Cat" not in names


def test_create_category_201(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.post(
        _cats_url(w.id),
        json={"name": "Honeymoon", "allocated_amount": 5000.0},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Honeymoon"
    assert data["allocated_amount"] == 5000.0
    assert data["wedding_id"] == w.id


def test_create_category_other_users_wedding_404(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_w = create_wedding(db_session, alice_id)

    bob_token = register_and_login(client, "bob@example.com")
    resp = client.post(
        _cats_url(alice_w.id),
        json={"name": "Intruder", "allocated_amount": 0},
        headers=_auth(bob_token),
    )
    assert resp.status_code == 404


def test_get_category(
    client, register_and_login, db_session, create_wedding, create_category, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    cat = create_category(db_session, w.id, name="Flowers")

    resp = client.get(_cat_url(w.id, cat.id), headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["name"] == "Flowers"


def test_patch_category_updates_only_provided(
    client, register_and_login, db_session, create_wedding, create_category, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    cat = create_category(db_session, w.id, name="Original", allocated_amount=2000.0)

    resp = client.patch(_cat_url(w.id, cat.id), json={"name": "Updated"}, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated"
    assert data["allocated_amount"] == 2000.0  # unchanged


def test_delete_category_cascades_expenses(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_category,
    create_expense,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    cat = create_category(db_session, w.id)
    for i in range(3):
        create_expense(db_session, cat.id, w.id, title=f"Expense {i}")

    resp = client.delete(_cat_url(w.id, cat.id), headers=_auth(token))
    assert resp.status_code == 204

    # Category gone
    resp = client.get(_cat_url(w.id, cat.id), headers=_auth(token))
    assert resp.status_code == 404

    # All expenses gone
    from app.models import Expense

    remaining = db_session.query(Expense).filter(Expense.category_id == cat.id).count()
    assert remaining == 0


def test_create_category_validates_negative_amount_422(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.post(
        _cats_url(w.id),
        json={"name": "Bad", "allocated_amount": -100},
        headers=_auth(token),
    )
    assert resp.status_code == 422


# ── Scaling ───────────────────────────────────────────────────────────────────


def test_scale_budget_doubles_amounts(client, register_and_login):
    token = register_and_login(client)
    resp = client.post(
        "/api/v1/weddings",
        json={**_VALID_WEDDING, "total_budget": 10000},
        headers=_auth(token),
    )
    wid = resp.json()["id"]

    cats_before = client.get(_cats_url(wid), headers=_auth(token)).json()
    amounts_before = {c["name"]: c["allocated_amount"] for c in cats_before}

    resp = client.post(_scale_url(wid), json={"new_total": 20000}, headers=_auth(token))
    assert resp.status_code == 200

    cats_after = client.get(_cats_url(wid), headers=_auth(token)).json()
    amounts_after = {c["name"]: c["allocated_amount"] for c in cats_after}

    for name, before in amounts_before.items():
        after = amounts_after[name]
        assert abs(after - before * 2) < 0.02, f"{name}: {before} → {after}"


def test_scale_budget_returns_count_and_totals(client, register_and_login):
    token = register_and_login(client)
    resp = client.post("/api/v1/weddings", json=_VALID_WEDDING, headers=_auth(token))
    wid = resp.json()["id"]

    resp = client.post(_scale_url(wid), json={"new_total": 30000}, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["new_total"] == 30000
    assert data["categories_scaled"] == 8
    assert "previous_total" in data


def test_scale_budget_zero_total_returns_422(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.post(_scale_url(w.id), json={"new_total": 0}, headers=_auth(token))
    assert resp.status_code == 422


# ── Expenses ──────────────────────────────────────────────────────────────────


def test_create_expense(
    client, register_and_login, db_session, create_wedding, create_category, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    cat = create_category(db_session, w.id)

    resp = client.post(
        _expenses_url(w.id),
        json={"category_id": cat.id, "title": "Deposit", "estimated_cost": 500.0},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Deposit"
    assert data["estimated_cost"] == 500.0
    assert data["wedding_id"] == w.id
    assert data["category_id"] == cat.id


def test_create_expense_with_other_weddings_category_returns_404(
    client, register_and_login, db_session, create_wedding, create_category, user_id_from_email
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_w = create_wedding(db_session, alice_id)
    alice_cat = create_category(db_session, alice_w.id)

    bob_token = register_and_login(client, "bob@example.com")
    bob_id = user_id_from_email(db_session, "bob@example.com")
    bob_w = create_wedding(db_session, bob_id)

    # Bob tries to create an expense referencing Alice's category
    resp = client.post(
        _expenses_url(bob_w.id),
        json={"category_id": alice_cat.id, "title": "Intruder"},
        headers=_auth(bob_token),
    )
    assert resp.status_code == 404


def test_create_expense_with_other_weddings_vendor_returns_404(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_category,
    create_vendor,
    user_id_from_email,
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_w = create_wedding(db_session, alice_id)
    alice_vendor = create_vendor(db_session, alice_w.id)

    bob_token = register_and_login(client, "bob@example.com")
    bob_id = user_id_from_email(db_session, "bob@example.com")
    bob_w = create_wedding(db_session, bob_id)
    bob_cat = create_category(db_session, bob_w.id)

    # Bob tries to create an expense referencing Alice's vendor
    resp = client.post(
        _expenses_url(bob_w.id),
        json={"category_id": bob_cat.id, "title": "Sneaky", "vendor_id": alice_vendor.id},
        headers=_auth(bob_token),
    )
    assert resp.status_code == 404


def test_list_expenses_returns_only_this_wedding(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_category,
    create_expense,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w1 = create_wedding(db_session, uid)
    w2 = create_wedding(db_session, uid)
    cat1 = create_category(db_session, w1.id)
    cat2 = create_category(db_session, w2.id)
    create_expense(db_session, cat1.id, w1.id, title="W1 Expense")
    create_expense(db_session, cat2.id, w2.id, title="W2 Expense")

    resp = client.get(_expenses_url(w1.id), headers=_auth(token))
    assert resp.status_code == 200
    titles = [e["title"] for e in resp.json()]
    assert "W1 Expense" in titles
    assert "W2 Expense" not in titles


def test_patch_expense_can_change_category_within_wedding(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_category,
    create_expense,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    cat1 = create_category(db_session, w.id, name="Cat 1")
    cat2 = create_category(db_session, w.id, name="Cat 2")
    expense = create_expense(db_session, cat1.id, w.id)

    resp = client.patch(
        _expense_url(w.id, expense.id),
        json={"category_id": cat2.id},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["category_id"] == cat2.id


def test_patch_expense_to_other_weddings_category_returns_404(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_category,
    create_expense,
    user_id_from_email,
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_w = create_wedding(db_session, alice_id)
    alice_cat = create_category(db_session, alice_w.id)

    bob_token = register_and_login(client, "bob@example.com")
    bob_id = user_id_from_email(db_session, "bob@example.com")
    bob_w = create_wedding(db_session, bob_id)
    bob_cat = create_category(db_session, bob_w.id)
    bob_expense = create_expense(db_session, bob_cat.id, bob_w.id)

    resp = client.patch(
        _expense_url(bob_w.id, bob_expense.id),
        json={"category_id": alice_cat.id},
        headers=_auth(bob_token),
    )
    assert resp.status_code == 404


def test_delete_expense(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_category,
    create_expense,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    cat = create_category(db_session, w.id)
    expense = create_expense(db_session, cat.id, w.id)

    resp = client.delete(_expense_url(w.id, expense.id), headers=_auth(token))
    assert resp.status_code == 204

    resp = client.get(_expense_url(w.id, expense.id), headers=_auth(token))
    assert resp.status_code == 404


# ── Summary ───────────────────────────────────────────────────────────────────


def test_summary_with_no_expenses(
    client, register_and_login, db_session, create_wedding, create_category, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    create_category(db_session, w.id, name="Venue", allocated_amount=3000.0)
    create_category(db_session, w.id, name="Food", allocated_amount=2000.0)

    resp = client.get(_summary_url(w.id), headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_allocated"] == 5000.0
    assert data["total_spent"] == 0.0
    assert data["total_remaining"] == 5000.0
    assert len(data["categories"]) == 2
    assert all(c["spent_amount"] == 0 for c in data["categories"])


def test_summary_with_expenses(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_category,
    create_expense,
    user_id_from_email,
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    cat = create_category(db_session, w.id, name="Venue", allocated_amount=1000.0)
    # actual_cost=300 counts toward spent; estimated_cost=500 does not
    create_expense(
        db_session, cat.id, w.id, title="Deposit", estimated_cost=500.0, actual_cost=300.0
    )

    resp = client.get(_summary_url(w.id), headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_spent"] == 300.0
    assert data["total_remaining"] == 700.0
    cat_summary = next(c for c in data["categories"] if c["category_name"] == "Venue")
    assert cat_summary["spent_amount"] == 300.0
    assert cat_summary["remaining"] == 700.0


def test_summary_other_users_wedding_returns_404(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_w = create_wedding(db_session, alice_id)

    bob_token = register_and_login(client, "bob@example.com")
    resp = client.get(_summary_url(alice_w.id), headers=_auth(bob_token))
    assert resp.status_code == 404
