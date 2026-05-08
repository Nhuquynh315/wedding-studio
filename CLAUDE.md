# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Backend — install + start
cd backend
uv venv                          # creates .venv using Python 3.12 (pinned in .python-version)
source .venv/bin/activate
uv pip install -e ".[dev]"
alembic upgrade head             # create/migrate SQLite DB
uvicorn api.main:app --reload --port 8000

# Alembic migrations
alembic revision --autogenerate -m "description"   # generate after model changes
alembic upgrade head
alembic downgrade -1

# Backend tests
pytest -q

# Frontend — install + start
cd frontend
npm install
npm run dev          # http://localhost:5173 (proxies /api → :8000)
npm run test         # Vitest unit tests
npm run e2e          # Playwright (auto-starts both servers)
npm run build        # production bundle → frontend/dist/
npx tsc --noEmit     # type-check without emitting
```

Environment variables (backend `.env`):
```
JWT_SECRET_KEY=<hex string>                        # required — openssl rand -hex 32
SQLALCHEMY_DATABASE_URL=sqlite:///instance/wedding_studio.db   # optional default
GEMINI_API_KEY=<key>                               # optional — AI theme generation
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

If the database was deleted, run `alembic upgrade head` then register a new account at `http://localhost:5173/register`.

## Architecture

**Backend** — FastAPI app at `backend/api/main.py`. Router modules under `backend/api/v1/`. Pydantic schemas under `backend/api/schemas/`. SQLAlchemy models in `backend/app/models.py` (pure SQLAlchemy, `declarative_base` — no Flask-SQLAlchemy). Alembic manages migrations in `backend/migrations/`.

**Models** (`backend/app/models.py`):

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

Relationships all use `cascade='all, delete-orphan'`. `WEDDING_STYLES`, `VENDOR_CATEGORIES`, `VENDOR_STATUSES`, `CHECKLIST_CATEGORIES`, `CHECKLIST_PRIORITIES` tuples define valid enum values — always validate against them. Always filter `Wedding` queries by `user_id` from the JWT (`require_wedding_access` dependency).

**Service layer** (`backend/api/services/`):

| File | Purpose |
|---|---|
| `ai_service.py` | Calls Gemini 2.5 Flash to generate wedding theme JSON |
| `csv_service.py` | Parses guest CSV uploads (all-or-nothing, 1 MB cap, UTF-8-BOM tolerant) |
| `checklist_service.py` | Seeds ~35 default planning tasks on wedding create |
| `budget_service.py` | Seeds 8 default budget categories on wedding create; exposes proportional rescaling |

**Frontend** — React SPA at `frontend/src/`. See `docs/architecture-frontend.md` for full details.

**Database**: SQLite in development (`backend/instance/wedding_studio.db`). Schema managed by Alembic — run `alembic upgrade head` on first setup and after every model change.

## Known refactor opportunities

**Vendor delete cascade (Phase 5):** `Expense.vendor_id` FK has no `ondelete="SET NULL"` at the DB level. The FastAPI `delete_vendor` route manually nullifies linked expenses before deleting the vendor. This application-level SET NULL should be replaced with a proper DB-level constraint (`ForeignKey("vendors.id", ondelete="SET NULL")`) in Phase 5 when migrating to Postgres.

**Profile + Password sections (Phase 5):** `SettingsPage` renders placeholder sections for profile editing and password change. The `PATCH /api/v1/auth/me` and password-change endpoints are not yet wired up in the frontend.

**Token refresh (Phase 5):** Expired JWTs show a toast + redirect to `/login`. Silent refresh using the stored `refresh_token` is not implemented.

## Verification policy

When making code changes that affect the UI:

1. Run type-check: `cd frontend && npx tsc --noEmit`
2. Run backend tests: `cd backend && pytest -q`
3. Smoke-test the API: `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/v1/health`
4. The user verifies the actual UI in their browser

Do NOT automate user logins or simulate browser sessions. The user does browser verification.

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

### Phase 4 — React + TypeScript frontend ✅ COMPLETE

Replaced Jinja templates with a React SPA. Removed the legacy Flask backend entirely. The FastAPI server now serves the built React assets (via `StaticFiles` mount at `/`) in addition to the JSON API.

**Architecture decisions documented in `docs/architecture-frontend.md`** — stack, API integration, state management, cache invalidation, optimistic updates, component architecture, form pattern, testing, known gaps.

#### Completed — 18 prompts across 2026-05-07 → 2026-05-08

| Prompt | Deliverable |
|---|---|
| 1–4 | Vite scaffold, Tailwind, React Router, AuthContext, token storage |
| 5 | Login page — React Hook Form + Zod, API error mapping, redirect-back |
| 6 | Layout shell — sidebar (desktop), mobile top bar + Sheet drawer, NavLink active styling |
| 6.5 | Registration page (added mid-session) |
| 7 | TanStack Query setup + Dashboard — 4 stat cards, `useActiveWedding`, query key factory |
| 8 | Guests page — table, search, RSVP filter, add/edit/delete dialogs, bulk RSVP, CSV import |
| 9 | Budget page — category cards, expense table, pie chart, add/edit/delete dialogs, proportional scale |
| 10 | Vendors page — card grid, status filter, add/edit/delete dialogs, deposit + payment tracking |
| 11 | Checklist page — grouped by category, priority badges, add/edit/delete, bulk-complete, optimistic toggle |
| 12 | Seating page — dnd-kit drag-and-drop, unassigned pool, table zones, add/edit/delete tables |
| 13 (fix) | `DeleteTableDialog` parse error (apostrophe in single-quoted string) |
| 13.5 | `react-is` peer dep + production build fix |
| 14 | Settings page — WeddingListSection with create/edit/delete wedding dialogs |
| 15 | Loading + error states audit — `QueryErrorState`, skeletons on all pages |
| 16 | Vitest + Playwright tests — unit tests for `daysUntil`, form schemas; e2e register→create wedding flow |
| 17 | Delete Flask backend — removed `app/`, `config.py`, `run.py`, Flask deps from `pyproject.toml`; rewrote `models.py` to pure SQLAlchemy; updated `migrations/env.py` and `tests/conftest.py` |
| 18 | Phase closeout — gitignore, `docs/architecture-frontend.md`, README, CLAUDE.md |

**Key patterns:**
- `npx shadcn@latest add` blocked by TS 6 peer dep conflict — Radix packages installed directly with `--legacy-peer-deps`, shadcn components hand-written
- All server state via TanStack Query; query keys in `src/lib/query-keys.ts`
- Optimistic updates on checklist toggle + seating assignment (onMutate snapshot → onError rollback → onSettled invalidate)
- `QueryErrorState` centralises error display; 401 branch clears tokens + dispatches `AUTH_EXPIRED_EVENT`
