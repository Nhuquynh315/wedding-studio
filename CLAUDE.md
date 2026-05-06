# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## System dependencies (macOS)

WeasyPrint (PDF generation) requires Pango, Cairo, and GLib system libraries. Install once via Homebrew:

```bash
brew install pango cairo glib
```

uv-managed Python (standalone distribution) does not inherit Homebrew's dyld search paths the way framework Pythons do. `DYLD_FALLBACK_LIBRARY_PATH` must be set so cffi can find `libgobject`, `libpango`, etc. This is already set in `backend/.env` (which Flask CLI auto-loads before importing the app). If you're on Intel Mac, change the path from `/opt/homebrew/lib` to `/usr/local/lib`.

## Commands

```bash
# Run development server (use port 5001 on macOS — port 5000 is taken by AirPlay Receiver)
flask run --port 5001

# Database migrations
flask db migrate -m "description"   # generate migration after model changes
flask db upgrade                     # apply pending migrations
flask db downgrade                   # roll back one migration

# Install dependencies (Python version pinned via backend/.python-version — Python 3.12)
cd backend
uv venv                      # creates .venv using the pinned 3.12 interpreter
uv pip install -e ".[dev]"   # installs all deps including dev extras
```

### Running Flask — directory matters

All `flask` commands must be run from `backend/`, not the repo root. `run.py` lives in `backend/` and is what Flask resolves as the app entry point — running from the repo root produces `Could not import 'run'`.

Canonical smoke-test sequence:

```bash
cd backend && source .venv/bin/activate && \
  flask --app run run --port 5001 --no-debugger
```

`FLASK_APP=run flask run --port 5001` is an equivalent alternative but `--app run` is the more explicit form and matches all migration commands (`flask --app run db upgrade`, etc.).

Environment variables are loaded from `.env`. Minimum required:
```
FLASK_ENV=development
SECRET_KEY=<any string>
DATABASE_URL=sqlite:///wedding_studio.db   # optional, this is the default
GEMINI_API_KEY=<key>                       # required for AI theme generation
```

## Development — test account

Seeded in `backend/instance/wedding_studio.db` (dev database, not committed):

- **Email:** `doe@gmail.com`
- **Password:** `12345678` — dev only, do not reuse anywhere real
- **Full name:** Doe

Test data attached to this account (one wedding, partners SHELL & SEA, date 2026-06-19):

| Data | Count |
|---|---|
| Guests | 101 |
| Checklist items | 36 |
| Budget categories | 8 |
| Wedding tables | 0 |
| Vendors | 0 |

If the database was deleted and recreated from migrations, re-register at `/register` — the schema is empty after a fresh `flask db upgrade`.

## Architecture

**Application factory** in `app/__init__.py` — `create_app(config_name)` accepts `'development'`, `'testing'`, or `'production'`. Config classes live in `config.py`. Extensions initialised at module level: `db`, `login_manager`, `migrate`, `csrf`, `limiter`.

**Blueprint layout:**
| Blueprint | File | Notes |
|---|---|---|
| `main_bp` | `app/routes/main.py` | Home page |
| `auth_bp` | `app/routes/auth.py` | Register, login, logout |
| `wedding_bp` | `app/routes/wedding.py` | Dashboard, create/edit wedding, activate wedding |
| `guests_bp` | `app/routes/guests.py` | Guest list, RSVP management, CSV/Excel import |
| `budget_bp` | `app/routes/budget.py` | Budget categories and expense tracking |
| `vendors_bp` | `app/routes/vendors.py` | Vendor management, contract tracking, payments |
| `checklist_bp` | `app/routes/checklist.py` | Task/timeline checklist |
| `seating_bp` | `app/routes/seating.py` | Table layout and guest seating assignment |
| `settings_bp` | `app/routes/settings.py` | User profile and notification preferences |

All blueprints except `main_bp` are re-exported through `app/routes/__init__.py`.

**Models** (`app/models.py`):

| Model | Table | Purpose |
|---|---|---|
| `User` | `users` | Authentication, profile, avatar colour |
| `Wedding` | `weddings` | Core wedding record; owns all other data |
| `Guest` | `guests` | Attendee list, RSVP status, meal preference, table assignment |
| `ChecklistItem` | `checklist_items` | Planning task with category, due date, priority |
| `BudgetCategory` | `budget_categories` | Named budget envelope with allocated amount |
| `Expense` | `expenses` | Line-item cost linked to a category and optionally a vendor |
| `Vendor` | `vendors` | Supplier with contract, deposit, final-payment tracking |
| `WeddingTable` | `wedding_tables` | Physical table with capacity, shape, and drag-and-drop position |
| `Design` | `designs` | AI-generated invitation HTML + PDF file path |

Relationships all use `cascade='all, delete-orphan'`. `WEDDING_STYLES`, `VENDOR_CATEGORIES`, `VENDOR_STATUSES`, `CHECKLIST_CATEGORIES`, `CHECKLIST_PRIORITIES` tuples define valid enum values — always validate against them. Always filter `Wedding` queries by `user_id=current_user.id` (ownership).

**Security layer:**
- `CSRFProtect` — active globally; every form needs `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`. CSRF error renders `app/templates/errors/csrf.html`.
- `Flask-Limiter` — `limiter` exported from `app/__init__.py`; applied per-route with `@limiter.limit(...)`.
- `db.session.commit()` calls are wrapped in `try/except` with `db.session.rollback()` on failure.

**Service layer** (`app/services/`):

| File | Status | Purpose |
|---|---|---|
| `ai_service.py` | Implemented | Calls Gemini 2.5 Flash to generate wedding theme JSON (colour palette, font suggestions, invitation wording, decor ideas) |
| `pdf_service.py` | Implemented | Renders invitation HTML template and converts to PDF via WeasyPrint; persists a `Design` record |
| `csv_service.py` | Implemented | Parses guest CSV and Excel (.xlsx) uploads with column aliasing and validation |
| `checklist_service.py` | Implemented | Seeds a new wedding with ~35 default planning tasks calculated relative to the wedding date |
| `budget_service.py` | Implemented | Seeds a new wedding with 8 default budget categories scaled to the wedding's `total_budget` (falls back to $20k if unset); also exposes `scale_existing_categories` for proportional rescaling |

**Templates** extend `base.html` using `{% block content %}`, `{% block extra_css %}`, `{% block extra_js %}`. Wedding templates live in `app/templates/wedding/`. Auth templates in `app/templates/auth/`. Error templates in `app/templates/errors/`. Brand CSS variables (rose palette) defined under `:root` in `app/static/css/style.css`, loaded globally by `base.html`.

**Fonts:** Lora (headings) and DM Sans (body/UI) loaded via Google Fonts in `base.html`. Self-hosted fallback for Playfair Display is in `app/static/fonts/`.

**Database**: SQLite in development (`instance/wedding_studio.db`). Schema is managed exclusively by Flask-Migrate — `db.create_all()` has been removed. Run `flask db upgrade` on first setup and after every model change.

## Known refactor opportunities

**Authorization-check-and-discard pattern (Phase 3):** Six routes call `get_wedding_or_403(wedding_id)` purely for its 403-raising side effect without using the returned `Wedding` object (`budget.py`, `checklist.py`, `seating.py` ×3, `vendors.py`). These should be consolidated into a decorator (e.g. `@require_wedding_ownership`) in Phase 3 when the route layer is refactored.

**Vendor delete cascade (Phase 5):** `Expense.vendor_id` FK has no `ondelete="SET NULL"` at the DB level. The FastAPI `delete_vendor` route manually nullifies linked expenses before deleting the vendor. This application-level SET NULL should be replaced with a proper DB-level constraint (`ForeignKey("vendors.id", ondelete="SET NULL")`) in Phase 5 when migrating to Postgres.

## Verification policy

When making code changes that affect the UI, the verification workflow is:

1. Make the code change
2. Run a basic smoke test from the command line:
     ```bash
     curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:5001/<route>
     ```
   Acceptable: 200, 302 (redirect to login), 401, 403. NOT 500.
3. Commit if smoke test passes
4. The user verifies the actual UI in their real browser

Do NOT automate user logins, simulate browser sessions, scrape authenticated HTML, or write Python scripts that POST to `/login`. The user does browser verification; Claude Code confirms only that the server doesn't crash. If a change can't be verified without a real browser, that's fine — stop after the smoke test passes and tell the user what page to load and what to look for.

## Refactor status

### Phase 1 — Repo hygiene & tooling ✅ COMPLETE

Completed across 13 commits (`d4e7b00` → `739ebc4`):
- Moved Flask app into `backend/` for future monorepo layout
- Replaced `requirements.txt` with `pyproject.toml` managed by uv; Python pinned to 3.12 via `backend/.python-version`
- Added `.pre-commit-config.yaml` running Ruff (lint + import sort) and Black (format) on every commit
- Cleaned up repo: comprehensive `.gitignore`, removed committed `venv/`/`instance/`/`uploads/` artifacts
- Fixed B023 stale-closure bug in `csv_service.py`; removed unused `wedding =` assignments from 6 routes
- Fixed WeasyPrint system library path for uv-managed Python on macOS via `DYLD_FALLBACK_LIBRARY_PATH` in `.env`
- Added `warnings.warn` when `SECRET_KEY` falls back to the dev default

### Phase 2 — Extract inline JS/CSS from Jinja templates ✅ COMPLETE

- Static asset infrastructure landed: `csrf.js` global CSRF helper, `ASSET_VERSION` cache-busting via git SHA, and `<meta name="csrf-token">` in `base.html`
- Extracted `base.html` global styles → `static/css/base.css` (~317 lines)
- Extracted `dashboard.html` styles → `static/css/dashboard.css` (~219 lines)
- Remaining template extractions (settings, checklist, vendors, budget, detail, seating) deferred to Phase 4 — those templates will be replaced by React components rather than refactored as Jinja
- Opportunistic UX fixes shipped during Phase 2: RSVP status pills, budget proportional scaling, dashboard response rate calculation

### Phase 3 — Port backend to FastAPI

Migrate Flask routes to FastAPI with Pydantic schemas for request/response validation. SQLAlchemy models and Alembic migrations are reused as-is — only the route layer changes. The Jinja templates will be temporarily kept (served by a thin FastAPI/Starlette static mount) until Phase 4 replaces them with React. The output of Phase 3 is a JSON API at `/api/*` with auto-generated OpenAPI docs at `/api/docs`.

#### Session log — 2026-05-03

- Started Phase 3 (prompt 1 of 15 complete): FastAPI scaffold with `/api/v1/health` endpoint
- Added deps: `fastapi`, `uvicorn`, `python-jose`, `passlib`, `pydantic-settings`
- `JWT_SECRET_KEY` generated and written to `.env` (not `.env.example`)
- Commit: `f6d6359`

Prompts 2, 3, 4 of 15 complete:

- FastAPI now reads same DB as Flask via shared `SessionLocal` (matched user counts: 1 = 1)
- Discovered Flask-SQLAlchemy / raw SQLAlchemy URL incompatibility; fixed via separate `SQLALCHEMY_DATABASE_URL` env var
- pytest infrastructure landed: 8 tests passing in <2s
- Auth schemas defined (`UserCreate`, `UserLogin`, `UserPublic`, `Token`, `TokenPayload`) in `api/schemas/auth.py`
- Password hashing implemented: bcrypt for new hashes, werkzeug for legacy Flask scrypt hashes
- Removed `passlib` dependency (unmaintained, broken with modern bcrypt)
- `needs_rehash()` helper added for transparent legacy user migration on login
- Commits: `0ee3ce8`, `9d42259`, `8ad0a52`, `0d5053b`

#### Tomorrow — Prompt 5

JWT helpers (`create_access_token`, `create_refresh_token`, `verify_token`) in `api/core/security.py`.

#### Session log — 2026-05-04

Prompts 5, 6 of 15 complete:

- JWT primitives landed: `create_access_token`, `create_refresh_token`, `decode_token` in `api/core/security.py` using python-jose; `InvalidTokenError` raised on any failure mode
- 4 auth endpoints wired: `POST /register`, `POST /login`, `POST /refresh`, `GET /me`
- `get_current_user` dependency in `api/core/deps.py` — reusable by all protected endpoints
- Test count now 28 (up from 15) — 13 auth tests including duplicate-email, token-type confusion, missing-token, garbage-token
- Per-test in-memory SQLite via `dependency_overrides` — tests no longer pollute dev DB
- Browser-verified at `/api/v1/docs`: register → login → `/me` chain works end-to-end with real JWT
- Commits: `ef11425`, `a75f4fd`

Prompts 7, 8, 9a, 9b of 15 complete:

- `require_wedding_access` dependency landed in `api/core/deps.py` — returns 404 (not 403) to hide resource existence; addresses Phase 1 known debt about `get_wedding_or_403`
- Wedding CRUD endpoints: list, create, get, patch, delete under `/api/v1/weddings`
- Guest CRUD endpoints (9a): list, create, get, patch, delete under `/api/v1/weddings/{wedding_id}/guests`; `RSVPStatus` StrEnum validates pending/confirmed/declined
- Cursor pagination + RSVP filter (9b): `GET /api/v1/weddings/{wedding_id}/guests` now returns `{"items": [...], "next_cursor": str|null, "limit": int}`; default limit 50, max 200; reusable cursor utilities in `api/core/pagination.py` (will be used by vendors and checklist)
- Caught and fixed naming bug: `cursor_or_400` → `cursor_or_422` (helper raises 422, name now matches)
- All edge cases tested: limit bounds, invalid cursor (422), empty page, filter+pagination combined, missing-id-in-payload
- Test count now 67 (up from 28)
- Commits: `672c0b2`, `4da93b0`, `d4d680a`

#### Tomorrow — Prompts 9c, 9d, 10–13

- 9c — RSVP bulk update endpoint (mark whole group as confirmed/etc)
- 9d — CSV import endpoint
- After that, Prompts 10–13 (budget, vendors, checklist, seating) — largely mechanical applications of established patterns
