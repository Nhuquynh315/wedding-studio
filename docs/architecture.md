# Phase 3 Architecture — FastAPI JSON API

This document captures the key design decisions made during Phase 3 of the Wedding Studio port. It is intended as a reference for Phase 4 (React frontend) and Phase 5 (production hardening) contributors.

## Table of contents

1. [Core decisions](#core-decisions)
   - [JWT over sessions](#jwt-over-sessions)
   - [Backward-compatible password hashing](#backward-compatible-password-hashing)
   - [Authorization via dependency injection](#authorization-via-dependency-injection)
   - [Resource cloaking (404 over 403)](#resource-cloaking-404-over-403)
   - [Three-schema pattern per resource](#three-schema-pattern-per-resource)
   - [Cursor pagination](#cursor-pagination)
   - [Application-level SET NULL cascades](#application-level-set-null-cascades)
   - [RFC 7807 error format](#rfc-7807-error-format)
   - [Test isolation](#test-isolation)
2. [What's deliberately NOT here](#whats-deliberately-not-here)
3. [Phase 5 follow-ups (collected debts)](#phase-5-follow-ups-collected-debts)

---

## Core decisions

### JWT over sessions

The legacy Flask app uses session cookies. The FastAPI port uses JWT in `Authorization: Bearer` headers. Reasons:

- **Cross-origin friendliness.** When the Phase 4 React frontend hits the API across an origin boundary (e.g., `app.example.com` → `api.example.com`), JWT in headers avoids the CORS-with-credentials dance that session cookies require.
- **Stateless.** No session table to maintain, no sticky sessions in load-balanced deploys.
- **Industry-standard for APIs.** Anyone integrating against this API will expect Bearer tokens.

Trade-offs accepted: token revocation requires either short-lived tokens (15-min access tokens here) or a Redis-backed blocklist (deferred). Refresh tokens (7-day) handle the UX cost of frequent re-auth.

### Backward-compatible password hashing

Legacy Flask users have werkzeug scrypt password hashes in the shared database. Rather than forcing every user to reset their password, the API verifies against bcrypt OR werkzeug formats (`api/core/security.py::verify_password` checks the prefix to route to the correct verifier).

On successful login with a legacy hash, the route silently rehashes with bcrypt and updates the row (`api/v1/auth.py::login`'s `needs_rehash` check). Over time, all active users migrate to bcrypt without operator intervention.

### Authorization via dependency injection

Two reusable FastAPI dependencies handle the auth chain:

- **`get_current_user`** — extracts and validates the Bearer token, returns the User row, raises 401 on any failure
- **`require_wedding_access`** — extracts the `{wedding_id}` path parameter, fetches the Wedding, verifies it's owned by the current user, returns the Wedding row

Every wedding-scoped endpoint declares `wedding: Wedding = Depends(require_wedding_access)` in its signature. FastAPI handles auth + lookup + ownership check in one shot. ~30+ endpoints inherit this for free.

### Resource cloaking (404 over 403)

When a request targets a resource the current user doesn't own, the API returns 404 instead of 403. Reasoning: 403 leaks the existence of the resource. With 404, an attacker cannot enumerate wedding IDs to learn which exist.

Tested explicitly: `test_other_user_cannot_access_wedding`, `test_get_guest_from_wrong_wedding_returns_404`, etc.

### Three-schema pattern per resource

Each resource has three Pydantic schemas:

- `XxxCreate` — input for POST. Required fields are required; no `id`, `created_at`, etc.
- `XxxUpdate` — input for PATCH. All fields optional. The route uses `model_dump(exclude_unset=True)` to apply only provided fields (true PATCH semantics, not PUT-with-defaults).
- `XxxPublic` — response shape. Uses `ConfigDict(from_attributes=True)` to auto-convert from SQLAlchemy models. Permissive on validation (e.g., `email: str` not `EmailStr`) so legacy malformed data doesn't crash responses.

### Cursor pagination

Implemented for guests (`GET /api/v1/weddings/{w}/guests`). Cursor is base64-encoded JSON: `{"id": <last_seen_id>}`. Opaque to clients — pass back what the server sent.

Why cursor over offset:

- **No page drift** when items are added/removed mid-session
- **Constant-time** on any page (offset gets slow on large datasets)

Reusable utility in `api/core/pagination.py`. The encoding function trims base64 padding for cleaner URLs and re-adds it on decode (some HTTP clients mangle trailing `=`).

### Application-level SET NULL cascades

The Vendor and WeddingTable resources have related rows (`Expense.vendor_id`, `Guest.table_id`) that should null out when the parent is deleted. The model FKs lack `ondelete="SET NULL"`, so the routes manually `UPDATE ... SET ... = NULL` before `db.delete()`.

This is a deliberate Phase 3 decision: model schema changes require migrations, which we agreed not to do during Phase 3. The Phase 5 deploy adds the DB-level constraints as defense-in-depth (and removes the manual nullify in the routes).

### RFC 7807 error format

All error responses use `application/problem+json`:

```json
{
  "type": "about:blank",
  "title": "Not Found",
  "status": 404,
  "detail": "Wedding not found",
  "instance": "/api/v1/weddings/99999"
}
```

Plus extension fields for context: `errors` (Pydantic validation breakdowns per field), `row_errors` (CSV import per-row failures).

Three centralized exception handlers in `api/core/errors.py` handle `HTTPException`, `RequestValidationError`, and the generic `Exception` fallback (which doesn't leak stack traces).

### Test isolation

Each test gets a fresh in-memory SQLite database via pytest fixtures + FastAPI's `dependency_overrides`. Tests can freely create users/weddings/guests without polluting the dev DB.

`conftest.py` provides reusable factory fixtures: `register_and_login`, `create_wedding`, `create_guest`, `create_vendor`, `create_category`, `create_expense`, `create_table`, `create_checklist_item`. Every test composing these reads cleanly.

171 tests run in under 90 seconds.

---

## What's deliberately NOT here

- **Capacity enforcement on table assignments.** Real wedding seating has too many edge cases ("the kids' table also fits one supervising adult") for strict API-level enforcement to help. UX layer warns; API stores what's asked.
- **Token revocation/blocklist.** Acceptable trade-off given 15-minute access TTLs. Phase 6 production hardening would add a Redis-backed blocklist if needed.
- **Rate limiting.** Inherited from Flask via Flask-Limiter (which uses in-memory storage and warns about it on every smoke test). Phase 5 deploy will need a proper backend (Redis or similar).
- **Email verification.** Users register and immediately have full access. Acceptable for a portfolio app; production would require email confirmation before sensitive actions.
- **Audit logging.** No "who did what when" tracking on mutations. Out of scope for Phase 3.

---

## Phase 5 follow-ups (collected debts)

- Add `ondelete="SET NULL"` to `Expense.vendor_id` and `Guest.table_id` FK relationships; remove the manual nullify in route handlers
- Migrate `Expense.actual_cost` / `estimated_cost` from Float to Decimal or integer cents (float arithmetic for money is incorrect)
- Replace Flask-Limiter's in-memory storage with Redis
- PostgreSQL migration (currently SQLite)
- Add a token blocklist for explicit logout / token revocation
- Rate limiting per-IP on auth endpoints
