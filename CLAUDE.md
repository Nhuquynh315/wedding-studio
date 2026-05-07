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

### Phase 3 — Port backend to FastAPI ✅ COMPLETE

Migrated Flask routes to FastAPI with Pydantic schemas. SQLAlchemy models and Alembic migrations reused as-is. Output: JSON API at `/api/v1/*` with OpenAPI docs at `/api/v1/docs`. 171 tests passing.

**Architecture decisions documented in `docs/architecture.md`** — JWT auth, backward-compatible password hashing, resource cloaking (404 over 403), three-schema pattern, cursor pagination, application-level SET NULL cascades, RFC 7807 errors, test isolation.

#### Completed — 14 prompts across 2026-05-03 → 2026-05-06

| Prompt | Deliverable | Tests |
|---|---|---|
| 1 | FastAPI scaffold, `/api/v1/health` | 8 |
| 2–4 | pytest infra, auth schemas, bcrypt + werkzeug password hashing | 28 |
| 5–6 | JWT primitives, auth endpoints (register/login/refresh/me) | 42 |
| 7–8 | `require_wedding_access` dep, wedding CRUD | 56 |
| 9a | Guest CRUD | 67 |
| 9b | Cursor pagination + RSVP filter | 80 |
| 9c | Bulk RSVP update | 95 |
| 9d | CSV import (all-or-nothing, 1 MB cap, UTF-8-BOM tolerant) | 115 |
| 10 | Budget API: categories, expenses, scaling, summary; auto-seed on wedding create | 129 |
| 11 | Vendors API; application-level SET NULL on expense.vendor_id | 149 |
| 12 | Checklist API; bulk-complete; `is_completed` + `completed_at` sync | 165 |
| 13 | Seating API; `/tables/with-guests` (joinedload); SET NULL on guest.table_id | 165 |
| 14 | RFC 7807 error format; OpenAPI metadata; `docs/architecture.md` | 171 |

### Phase 4 — React + TypeScript frontend

Replace Jinja templates with a React SPA that consumes the Phase 3 API.

**Stack:** React 18 · TypeScript · Vite · React Query · React Router · Tailwind CSS

**Approach:** Build the frontend in `frontend/` in parallel with the still-running Flask server. Once the React app covers all pages, remove the Jinja templates. The FastAPI server serves both the API and the built React assets (via `StaticFiles` mount).

**Page targets:** Login/register, dashboard, guest list, budget, vendors, checklist, seating chart (drag-and-drop), settings, AI theme generator.

**Phase 4 follow-up from Phase 3 decisions:**
- Cursor pagination means the guest list needs a "load more" button, not traditional pages
- The `/tables/with-guests` endpoint was purpose-built for the seating chart UI — one call, full state
- The RFC 7807 error envelope means the frontend can reliably read `body.title` + `body.detail` for all error toasts

#### Session log — 2026-05-07

Phase 4 Prompts 5, 6, 6.5, 7 complete (4 prompts in one session):

- **Prompt 5:** Login form — React Hook Form + Zod validation, API error mapping (401/422/other), redirect-back via `location.state.from`
- **Prompt 6:** Layout shell — 256px sidebar (desktop) + mobile top bar with hamburger Sheet drawer, 7 nav items with lucide icons, NavLink active styling, UserMenu with avatar initials + dropdown
- **Prompt 6.5:** Registration page — added mid-session, not in original 18-prompt plan; full_name + email + password + confirm_password, Zod `.refine()` for password match, auto-login after register (backend returns UserPublic not Token), reciprocal login↔register links
- **Prompt 7:** TanStack Query + Dashboard — QueryClient (5min stale / 10min gc / 1 retry), centralized query key factory (`src/lib/query-keys.ts`), devtools wired in dev; 4 stat cards (guests + RSVP bar, response rate, days until wedding, budget spent/allocated), `useActiveWedding` hook persisting active ID in localStorage

4 commits ahead of previous session checkpoint (`666785c` → `6e320c6`).

**Two patterns established for the rest of Phase 4:**

1. **Manual shadcn workaround** — TS 6 peer dep conflict prevents `npx shadcn@latest add` from running (internal `npm install` fails). Pattern: install Radix packages directly with `--legacy-peer-deps`, hand-write the shadcn wrapper matching the New York style source. Components written so far: Button, Input, Label, Card, Sheet, DropdownMenu, Avatar, Skeleton.
2. **TanStack Query for all server state** — every data fetch goes through `useQuery`; query keys centralized in `src/lib/query-keys.ts` for namespace invalidation; each card/section owns its query so they fetch in parallel and fail independently.

**Next:** Prompt 8 — Guests page. Virtualized table, search, RSVP filter, edit-in-place. Estimated 2.5–3 hours; should be its own session.
