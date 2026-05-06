def test_404_uses_rfc7807_envelope(client, register_and_login):
    token = register_and_login(client)
    resp = client.get(
        "/api/v1/weddings/99999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404
    body = resp.json()
    assert body["type"] == "about:blank"
    assert body["title"] == "Not Found"
    assert body["status"] == 404
    assert body["instance"] == "/api/v1/weddings/99999"


def test_404_content_type_is_problem_json(client, register_and_login):
    token = register_and_login(client)
    resp = client.get(
        "/api/v1/weddings/99999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.headers["content-type"].startswith("application/problem+json")


def test_401_preserves_www_authenticate_header(client):
    """When auth fails, the WWW-Authenticate header must still be set
    so OAuth2 clients know how to authenticate."""
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "www-authenticate" in {k.lower() for k in resp.headers}


def test_422_validation_errors_include_structured_field(client, register_and_login):
    token = register_and_login(client)
    resp = client.post(
        "/api/v1/weddings",
        json={},  # missing required fields
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["title"] == "Unprocessable Entity"
    assert "errors" in body
    assert isinstance(body["errors"], list)
    assert len(body["errors"]) > 0
    first = body["errors"][0]
    assert "loc" in first
    assert "msg" in first
    assert "type" in first


def test_409_conflict_envelope(client):
    """Register the same email twice → 409 Conflict in RFC 7807 shape."""
    payload = {"email": "alice@example.com", "password": "supersecret123", "full_name": "Alice"}
    client.post("/api/v1/auth/register", json=payload)
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409
    body = resp.json()
    assert body["title"] == "Conflict"
    assert body["status"] == 409
    assert "detail" in body


def test_csv_import_error_envelope_has_row_errors_at_top_level(
    client, register_and_login, db_session, create_wedding, user_id_from_email
):
    """row_errors is promoted from detail.row_errors to a top-level RFC 7807 extension field."""
    token = register_and_login(client)
    user_id = user_id_from_email(db_session, "alice@example.com")
    wedding = create_wedding(db_session, user_id)

    csv = b"full_name,email\nAlice,not-an-email\n"
    resp = client.post(
        f"/api/v1/weddings/{wedding.id}/guests/import",
        files={"file": ("guests.csv", csv, "text/csv")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["title"] == "Bad Request"
    assert "row_errors" in body  # top-level, not nested under "detail"
    assert isinstance(body["row_errors"], list)
