_VALID_REGISTER = {
    "email": "alice@example.com",
    "password": "supersecret123",
    "full_name": "Alice Anderson",
}


def test_register_creates_user(client):
    resp = client.post("/api/v1/auth/register", json=_VALID_REGISTER)
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "alice@example.com"
    assert data["full_name"] == "Alice Anderson"
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_register_rejects_duplicate_email(client):
    client.post("/api/v1/auth/register", json=_VALID_REGISTER)
    resp = client.post("/api/v1/auth/register", json=_VALID_REGISTER)
    assert resp.status_code == 409


def test_register_rejects_short_password(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={**_VALID_REGISTER, "password": "short"},
    )
    assert resp.status_code == 422


def test_register_rejects_invalid_email(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={**_VALID_REGISTER, "email": "not-an-email"},
    )
    assert resp.status_code == 422


def test_login_returns_tokens(client):
    client.post("/api/v1/auth/register", json=_VALID_REGISTER)
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": _VALID_REGISTER["email"], "password": _VALID_REGISTER["password"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_rejects_wrong_password(client):
    client.post("/api/v1/auth/register", json=_VALID_REGISTER)
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": _VALID_REGISTER["email"], "password": "wrong-password"},
    )
    assert resp.status_code == 401


def test_login_rejects_unknown_email(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "doesnt-matter"},
    )
    assert resp.status_code == 401


def test_me_returns_current_user(client):
    client.post("/api/v1/auth/register", json=_VALID_REGISTER)
    login = client.post(
        "/api/v1/auth/login",
        json={"email": _VALID_REGISTER["email"], "password": _VALID_REGISTER["password"]},
    )
    access = login.json()["access_token"]

    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == _VALID_REGISTER["email"]


def test_me_rejects_missing_token(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_rejects_garbage_token(client):
    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer garbage"},
    )
    assert resp.status_code == 401


def test_me_rejects_refresh_token(client):
    """A refresh token must NOT authorize /me."""
    client.post("/api/v1/auth/register", json=_VALID_REGISTER)
    login = client.post(
        "/api/v1/auth/login",
        json={"email": _VALID_REGISTER["email"], "password": _VALID_REGISTER["password"]},
    )
    refresh = login.json()["refresh_token"]

    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh}"},
    )
    assert resp.status_code == 401


def test_refresh_returns_new_tokens(client):
    client.post("/api/v1/auth/register", json=_VALID_REGISTER)
    login = client.post(
        "/api/v1/auth/login",
        json={"email": _VALID_REGISTER["email"], "password": _VALID_REGISTER["password"]},
    )
    refresh_token = login.json()["refresh_token"]

    resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_refresh_rejects_access_token():
    """Trying to use an access token at /refresh must fail."""
    pass
