from datetime import UTC

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


# ── PATCH /auth/me ────────────────────────────────────────────────────────────


def _register_and_token(
    client, email=_VALID_REGISTER["email"], password=_VALID_REGISTER["password"]
):
    client.post(
        "/api/v1/auth/register", json={**_VALID_REGISTER, "email": email, "password": password}
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return login.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_update_me_changes_full_name(client):
    token = _register_and_token(client)
    resp = client.patch("/api/v1/auth/me", json={"full_name": "New Name"}, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "New Name"

    me = client.get("/api/v1/auth/me", headers=_auth(token))
    assert me.json()["full_name"] == "New Name"


def test_update_me_changes_email(client):
    token = _register_and_token(client)
    resp = client.patch("/api/v1/auth/me", json={"email": "new@example.com"}, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["email"] == "new@example.com"

    me = client.get("/api/v1/auth/me", headers=_auth(token))
    assert me.json()["email"] == "new@example.com"


def test_update_me_partial(client):
    """PATCHing only full_name must leave email unchanged."""
    token = _register_and_token(client)
    original_email = _VALID_REGISTER["email"]

    resp = client.patch(
        "/api/v1/auth/me", json={"full_name": "Partial Update"}, headers=_auth(token)
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == original_email
    assert resp.json()["full_name"] == "Partial Update"


def test_update_me_duplicate_email_rejected(client):
    """User A cannot PATCH to user B's email."""
    token_a = _register_and_token(client, email="a@example.com")
    client.post(
        "/api/v1/auth/register",
        json={**_VALID_REGISTER, "email": "b@example.com"},
    )

    resp = client.patch("/api/v1/auth/me", json={"email": "b@example.com"}, headers=_auth(token_a))
    assert resp.status_code == 409


def test_update_me_same_email_ok(client):
    """Re-submitting one's own email (with a name change) must not 409."""
    token = _register_and_token(client)
    own_email = _VALID_REGISTER["email"]

    resp = client.patch(
        "/api/v1/auth/me",
        json={"email": own_email, "full_name": "Same Email Fine"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Same Email Fine"


def test_update_me_requires_auth(client):
    resp = client.patch("/api/v1/auth/me", json={"full_name": "No Token"})
    assert resp.status_code == 401


# ── POST /auth/change-password ────────────────────────────────────────────────


def test_change_password_success(client):
    token = _register_and_token(client)
    old_password = _VALID_REGISTER["password"]
    new_password = "newpassword999"

    resp = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": old_password, "new_password": new_password},
        headers=_auth(token),
    )
    assert resp.status_code == 204

    # Old password no longer works
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": _VALID_REGISTER["email"], "password": old_password},
    )
    assert bad_login.status_code == 401

    # New password works
    good_login = client.post(
        "/api/v1/auth/login",
        json={"email": _VALID_REGISTER["email"], "password": new_password},
    )
    assert good_login.status_code == 200


def test_change_password_wrong_current(client):
    token = _register_and_token(client)

    resp = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "wrong-password", "new_password": "newpassword999"},
        headers=_auth(token),
    )
    assert resp.status_code == 400

    # Original password still works — hash was NOT changed
    good_login = client.post(
        "/api/v1/auth/login",
        json={"email": _VALID_REGISTER["email"], "password": _VALID_REGISTER["password"]},
    )
    assert good_login.status_code == 200


def test_change_password_too_short(client):
    token = _register_and_token(client)
    resp = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": _VALID_REGISTER["password"], "new_password": "short"},
        headers=_auth(token),
    )
    assert resp.status_code == 422


def test_change_password_requires_auth(client):
    resp = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "anything", "new_password": "newpassword999"},
    )
    assert resp.status_code == 401


# ── Token blocklist (Phase 8A) ────────────────────────────────────────────────


def _login_tokens(client):
    """Register alice and return (access_token, refresh_token)."""
    client.post("/api/v1/auth/register", json=_VALID_REGISTER)
    login = client.post(
        "/api/v1/auth/login",
        json={"email": _VALID_REGISTER["email"], "password": _VALID_REGISTER["password"]},
    )
    data = login.json()
    return data["access_token"], data["refresh_token"]


def test_refresh_blocklists_old_refresh_token(client):
    """After /refresh, the OLD refresh token is blocklisted and rejected."""
    _, old_refresh = _login_tokens(client)

    # First refresh — succeeds, blocklists old_refresh
    resp1 = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert resp1.status_code == 200

    # Second attempt with the same old token — must be rejected
    resp2 = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert resp2.status_code == 401
    assert "revoked" in resp2.json()["detail"].lower()


def test_logout_blocklists_refresh_token(client):
    """After /logout, the refresh token can't be used to refresh."""
    _, refresh = _login_tokens(client)

    logout_resp = client.post("/api/v1/auth/logout", json={"refresh_token": refresh})
    assert logout_resp.status_code == 204

    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 401


def test_logout_is_idempotent(client):
    """Calling /logout twice with the same token returns 204 both times."""
    _, refresh = _login_tokens(client)

    r1 = client.post("/api/v1/auth/logout", json={"refresh_token": refresh})
    r2 = client.post("/api/v1/auth/logout", json={"refresh_token": refresh})
    assert r1.status_code == 204
    assert r2.status_code == 204


def test_logout_with_garbage_token_returns_204(client):
    """/logout never errors — soft-fail on invalid tokens (nothing to revoke)."""
    resp = client.post("/api/v1/auth/logout", json={"refresh_token": "not.a.real.jwt"})
    assert resp.status_code == 204


def test_refresh_rejects_token_with_no_jti(client):
    """Refresh tokens issued before jti support get rejected — forces re-login."""
    from datetime import datetime, timedelta

    from jose import jwt

    from api.core.config import settings

    client.post("/api/v1/auth/register", json=_VALID_REGISTER)
    legacy_token = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(UTC) + timedelta(days=1),
            "type": "refresh",
            # no jti
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": legacy_token})
    assert resp.status_code == 401
    detail = resp.json()["detail"].lower()
    assert "identifier" in detail or "log in again" in detail


def test_refresh_rejects_garbage_token(client):
    """Garbage tokens fail signature verification, return 401."""
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "garbage"})
    assert resp.status_code == 401
