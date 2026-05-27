from datetime import UTC, datetime

from api.schemas.design import ColorEntry, FontPairing, GeneratedTheme
from api.services import ai_service as _ai_service
from api.services.ai_service import AIServiceUnavailable, AIServiceUnconfigured

_FAKE_THEME = GeneratedTheme(
    tagline="Blooms of Forever",
    color_palette=[
        ColorEntry(name="Rose", hex="#FF6B6B", role="Primary"),
        ColorEntry(name="Sage", hex="#7A8C5C", role="Secondary"),
        ColorEntry(name="Gold", hex="#D4A574", role="Accent"),
        ColorEntry(name="Cream", hex="#FAF7F2", role="Neutral"),
        ColorEntry(name="Blush", hex="#F2C4CE", role="Highlight"),
    ],
    font_suggestions=[
        FontPairing(heading="Pinyon Script", body="Lato", description="Script elegance."),
        FontPairing(heading="Cormorant Garamond", body="Lora", description="Classic serif."),
        FontPairing(heading="Raleway", body="Source Serif Pro", description="Modern sans."),
    ],
    invitation_text="join us as we begin our journey\ntogether as one",
    ceremony_time="4:00 PM",
    style_keywords=["romantic", "floral", "garden", "whimsical", "elegant"],
    decor_suggestions=["Trailing ivy", "Blush peonies", "Candlelit path", "Lace tablecloths"],
    rsvp_info="September 1, 2026",
)

_FAKE_THEME_JSON = _FAKE_THEME.model_dump_json()

_GENERATE_BODY = {
    "partner1_name": "Emma",
    "partner2_name": "James",
    "wedding_date": "2026-10-15",
    "location": "Adelaide Hills",
    "venue_name": "Stangate House",
    "style": "garden bohemian",
    "primary_color": "#D4A574",
    "secondary_color": "#7A8C5C",
    "tone": "Romantic",
}


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _designs_url(wid):
    return f"/api/v1/weddings/{wid}/designs"


def _design_url(wid, did):
    return f"/api/v1/weddings/{wid}/designs/{did}"


# ── POST ──────────────────────────────────────────────────────────────────────


def test_post_creates_design_201(
    client, register_and_login, db_session, create_wedding, user_id_from_email, monkeypatch
):
    monkeypatch.setattr(_ai_service, "generate_wedding_theme", lambda *a, **kw: _FAKE_THEME)

    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.post(_designs_url(w.id), json=_GENERATE_BODY, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["wedding_id"] == w.id
    assert data["design_type"] == "invitation"
    assert data["theme"]["tagline"] == _FAKE_THEME.tagline
    assert len(data["theme"]["color_palette"]) == 5
    assert len(data["theme"]["font_suggestions"]) == 3
    assert "id" in data
    assert "created_at" in data


def test_post_other_users_wedding_404(
    client, register_and_login, db_session, create_wedding, user_id_from_email, monkeypatch
):
    monkeypatch.setattr(_ai_service, "generate_wedding_theme", lambda *a, **kw: _FAKE_THEME)

    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_w = create_wedding(db_session, alice_id)

    bob_token = register_and_login(client, "bob@example.com")
    resp = client.post(_designs_url(alice_w.id), json=_GENERATE_BODY, headers=_auth(bob_token))
    assert resp.status_code == 404


def test_post_ai_unavailable_503(
    client, register_and_login, db_session, create_wedding, user_id_from_email, monkeypatch
):
    def _raise(*a, **kw):
        raise AIServiceUnavailable("upstream down")

    monkeypatch.setattr(_ai_service, "generate_wedding_theme", _raise)

    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.post(_designs_url(w.id), json=_GENERATE_BODY, headers=_auth(token))
    assert resp.status_code == 503
    assert "temporarily unavailable" in resp.json()["detail"]


def test_post_ai_unconfigured_503(
    client, register_and_login, db_session, create_wedding, user_id_from_email, monkeypatch
):
    def _raise(*a, **kw):
        raise AIServiceUnconfigured("no key")

    monkeypatch.setattr(_ai_service, "generate_wedding_theme", _raise)

    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    resp = client.post(_designs_url(w.id), json=_GENERATE_BODY, headers=_auth(token))
    assert resp.status_code == 503
    assert "not configured" in resp.json()["detail"]


# ── GET ───────────────────────────────────────────────────────────────────────


def test_list_designs_desc_order(
    client, register_and_login, db_session, create_wedding, create_design, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)

    older = create_design(
        db_session,
        w.id,
        html_content=_FAKE_THEME_JSON,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    newer = create_design(
        db_session,
        w.id,
        html_content=_FAKE_THEME_JSON,
        created_at=datetime(2026, 6, 1, tzinfo=UTC),
    )

    resp = client.get(_designs_url(w.id), headers=_auth(token))
    assert resp.status_code == 200
    ids = [d["id"] for d in resp.json()]
    assert ids == [newer.id, older.id]


# ── DELETE ────────────────────────────────────────────────────────────────────


def test_delete_removes_design(
    client, register_and_login, db_session, create_wedding, create_design, user_id_from_email
):
    token = register_and_login(client)
    uid = user_id_from_email(db_session, "alice@example.com")
    w = create_wedding(db_session, uid)
    design = create_design(db_session, w.id, html_content=_FAKE_THEME_JSON)

    resp = client.delete(_design_url(w.id, design.id), headers=_auth(token))
    assert resp.status_code == 204

    resp = client.get(_designs_url(w.id), headers=_auth(token))
    assert resp.json() == []


def test_delete_other_users_design_404(
    client, register_and_login, db_session, create_wedding, create_design, user_id_from_email
):
    register_and_login(client, "alice@example.com")
    alice_id = user_id_from_email(db_session, "alice@example.com")
    alice_w = create_wedding(db_session, alice_id)
    alice_design = create_design(db_session, alice_w.id, html_content=_FAKE_THEME_JSON)

    bob_token = register_and_login(client, "bob@example.com")
    resp = client.delete(_design_url(alice_w.id, alice_design.id), headers=_auth(bob_token))
    assert resp.status_code == 404
