def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _vendors_url(wid):
    return f"/api/v1/weddings/{wid}/vendors"


def _vendor_url(wid, vid):
    return f"/api/v1/weddings/{wid}/vendors/{vid}"


# ── CRUD ──────────────────────────────────────────────────────────────────────


def test_list_vendors_returns_only_this_wedding(
    client, register_and_login, db_session, create_wedding, create_vendor, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w1 = create_wedding(db_session, uid)
    w2 = create_wedding(db_session, uid)
    create_vendor(db_session, w1.id, business_name="W1 Vendor")
    create_vendor(db_session, w2.id, business_name="W2 Vendor")

    resp = client.get(_vendors_url(w1.id), headers=_auth(token))
    assert resp.status_code == 200
    names = [v["business_name"] for v in resp.json()]
    assert "W1 Vendor" in names
    assert "W2 Vendor" not in names


def test_create_vendor_201(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.post(
        _vendors_url(w.id),
        json={"business_name": "Floral Dreams", "category": "Flowers"},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["business_name"] == "Floral Dreams"
    assert data["category"] == "Flowers"
    assert data["status"] == "considering"
    assert data["wedding_id"] == w.id
    assert "id" in data


def test_create_vendor_other_users_wedding_404(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_w = create_wedding(db_session, alice_id)

    bob_token = register_and_login(client, "bob@example.com")
    resp = client.post(
        _vendors_url(alice_w.id),
        json={"business_name": "Intruder"},
        headers=_auth(bob_token),
    )
    assert resp.status_code == 404


def test_get_vendor(
    client, register_and_login, db_session, create_wedding, create_vendor, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    vendor = create_vendor(db_session, w.id, business_name="Caterers Inc")

    resp = client.get(_vendor_url(w.id, vendor.id), headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["business_name"] == "Caterers Inc"


def test_get_vendor_from_wrong_wedding_returns_404(
    client, register_and_login, db_session, create_wedding, create_vendor, user_id_from_email
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_w = create_wedding(db_session, alice_id)
    alice_vendor = create_vendor(db_session, alice_w.id)

    bob_token = register_and_login(client, "bob@example.com")
    bob_id = user_id_from_email(db_session, "bob@example.com")
    bob_w = create_wedding(db_session, bob_id)

    resp = client.get(_vendor_url(bob_w.id, alice_vendor.id), headers=_auth(bob_token))
    assert resp.status_code == 404


def test_patch_vendor_updates_only_provided(
    client, register_and_login, db_session, create_wedding, create_vendor, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    vendor = create_vendor(db_session, w.id, business_name="Original Name", status="considering")

    resp = client.patch(
        _vendor_url(w.id, vendor.id),
        json={"business_name": "Updated Name"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["business_name"] == "Updated Name"
    assert data["status"] == "considering"  # unchanged


def test_patch_vendor_can_change_status(
    client, register_and_login, db_session, create_wedding, create_vendor, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    vendor = create_vendor(db_session, w.id, status="considering")

    resp = client.patch(
        _vendor_url(w.id, vendor.id),
        json={"status": "booked"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "booked"


def test_delete_vendor(
    client, register_and_login, db_session, create_wedding, create_vendor, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    vendor = create_vendor(db_session, w.id)

    resp = client.delete(_vendor_url(w.id, vendor.id), headers=_auth(token))
    assert resp.status_code == 204

    resp = client.get(_vendor_url(w.id, vendor.id), headers=_auth(token))
    assert resp.status_code == 404


# ── Validation ────────────────────────────────────────────────────────────────


def test_create_vendor_invalid_status_returns_422(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.post(
        _vendors_url(w.id),
        json={"business_name": "Bad Status Co", "status": "contacted"},  # not a valid value
        headers=_auth(token),
    )
    assert resp.status_code == 422


def test_create_vendor_invalid_email_returns_422(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.post(
        _vendors_url(w.id),
        json={"business_name": "Bad Email Co", "email": "not-an-email"},
        headers=_auth(token),
    )
    assert resp.status_code == 422


def test_create_vendor_negative_quoted_price_returns_422(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.post(
        _vendors_url(w.id),
        json={"business_name": "Negative Price Co", "quoted_price": -500},
        headers=_auth(token),
    )
    assert resp.status_code == 422


# ── Status filter ─────────────────────────────────────────────────────────────


def test_list_vendors_filter_by_status(
    client, register_and_login, db_session, create_wedding, create_vendor, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    create_vendor(db_session, w.id, business_name="Booked One", status="booked")
    create_vendor(db_session, w.id, business_name="Booked Two", status="booked")
    create_vendor(db_session, w.id, business_name="Considering One", status="considering")

    resp = client.get(f"{_vendors_url(w.id)}?status=booked", headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(v["status"] == "booked" for v in data)


def test_list_vendors_filter_invalid_status_returns_422(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.get(f"{_vendors_url(w.id)}?status=contacted", headers=_auth(token))
    assert resp.status_code == 422


# ── Cascade behaviour ─────────────────────────────────────────────────────────


def test_delete_vendor_nullifies_expense_vendor_id(
    client,
    register_and_login,
    db_session,
    create_wedding,
    create_category,
    create_vendor,
    create_expense,
    user_id_from_email,
):
    """Deleting a vendor must not delete the linked expenses — it must set
    expense.vendor_id to None (application-level SET NULL, since the model FK
    lacks ON DELETE SET NULL)."""
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    cat = create_category(db_session, w.id)
    vendor = create_vendor(db_session, w.id, business_name="Photographer Ltd")
    expense = create_expense(db_session, cat.id, w.id, title="Photo Deposit", vendor_id=vendor.id)

    assert expense.vendor_id == vendor.id

    resp = client.delete(_vendor_url(w.id, vendor.id), headers=_auth(token))
    assert resp.status_code == 204

    from app.models import Expense

    db_session.expire_all()
    refreshed = db_session.query(Expense).filter(Expense.id == expense.id).first()
    assert refreshed is not None, "expense must still exist after vendor delete"
    assert refreshed.vendor_id is None, "vendor_id must be NULL after vendor delete"
