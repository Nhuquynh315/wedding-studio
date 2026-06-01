# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Backend — install + start
cd backend
uv venv                          # creates .venv using Python 3.12 (pinned in .python-version)
source .venv/bin/activate
uv pip install -e ".[dev]"
alembic upgrade head             # create/migrate Postgres DB
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
SQLALCHEMY_DATABASE_URL=postgresql+psycopg://<user>@localhost:5432/wedding_studio   # required
GEMINI_API_KEY=<key>                               # optional — AI invitation generation
SENTRY_DSN=<dsn>                                   # optional — error tracking
```

## Development — test account

Demo data is seeded via `python scripts/seed_demo.py` from the
`backend/` directory (venv active). Creates `demo@weddingstudio.app`
/ `DemoPass2026` with guests, vendors, budget, checklist, and
seating data. Idempotent — safe to re-run.

If the database was reset, run `alembic upgrade head` then
`python scripts/seed_demo.py`. Alternatively, register a fresh
account at `http://localhost:5173/register` for ad-hoc testing.

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
| `Design` | `designs` | AI-generated invitation theme (GeneratedTheme JSON stored in `html_content`); `pdf_file_path` column unused — Phase 7B uses browser print-to-PDF |

Relationships all use `cascade='all, delete-orphan'`. `WEDDING_STYLES`, `VENDOR_CATEGORIES`, `VENDOR_STATUSES`, `CHECKLIST_CATEGORIES`, `CHECKLIST_PRIORITIES` tuples define valid enum values — always validate against them. Always filter `Wedding` queries by `user_id` from the JWT (`require_wedding_access` dependency).

**Service layer**:

| File | Purpose |
|---|---|
| `api/services/ai_service.py` | Calls Gemini 2.5 Flash to generate wedding theme JSON (Pydantic structured outputs, 5 tones, 3 layouts) |
| `api/services/budget_seeding.py` | Seeds 8 default budget categories on wedding create; exposes proportional rescaling (called from `weddings.py` on POST and `budget.py` for rescale) |
| `api/core/csv_import.py` | Parses guest CSV uploads (all-or-nothing, 1 MB cap, UTF-8-BOM tolerant) |

Note: a Flask-era `checklist_service.py` (35 default planning tasks) was NOT ported to FastAPI. Creating a wedding seeds budget categories but no default checklist items.

**Frontend** — React SPA at `frontend/src/`. See `docs/architecture-frontend.md` for full details.

**Database**: PostgreSQL 16+ locally; AWS RDS PostgreSQL 18.3 in production. Schema managed by Alembic — run `alembic upgrade head` on first setup and after every model change. Tests use a real local Postgres database (`wedding_studio_test`) with per-test transaction rollback via savepoints.

## Known refactor opportunities (Phase 8)

**Token blocklist for logout** — JWTs remain valid until expiry after logout. Server-side blocklist (DB table) needed for real invalidation. Originally scoped for Phase 7B; reprioritized in favor of AI invitation feature.

**Default checklist seeding** — the Flask-era logic that seeded ~35 default planning tasks on wedding create was not ported during the FastAPI refactor. New weddings start with an empty checklist.

**AI invitation in-place edit** — currently the user generates an invitation and views/downloads it; no edit-in-place for tagline, RSVP date, or copy. Would need persistence back to `designs.html_content` and edge-case handling around layout switches.

**Frontend tests in CI workflow** — Vitest tests exist locally but aren't run by GitHub Actions on push.

**Docs-only commits trigger full deploy** — the deploy workflow doesn't use `paths-ignore`, so README/CLAUDE.md commits run the full ~13 min ECS rebuild.

**Bundle size code-split** — `index-*.js` exceeds 1 MB minified (chunk-size warning pre-existing since Phase 5).

**Sentry spike protection + allowed-domains** — currently using Sentry defaults; not explicitly configured.

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

Migrated Flask routes to FastAPI with Pydantic schemas. SQLAlchemy models and Alembic migrations reused as-is. Output: JSON API at `/api/v1/*` with OpenAPI docs at `/api/v1/docs`. 171 tests passing (188 after Phase 7B added designs router tests).

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

### Phase 5 — Production deployment to AWS ✅ COMPLETE

Backend deployed to ECS Fargate behind ALB (provisioned by ECS Express Mode). Frontend deployed to Vercel. Database on RDS PostgreSQL 18.3. Secrets in AWS Secrets Manager.

**Architecture decisions documented in `docs/architecture.md`** — Docker image build, ECR registry, ECS Express Mode (over App Runner — deprecation pivot), RDS public-but-firewalled with SSL, CORS configuration, environment-variable injection from Secrets Manager at task start.

Key blockers solved: App Runner deprecation pivot to ECS, IAM Secrets Manager `kms:Decrypt` permission, arm64/amd64 architecture mismatch (build target amd64), RDS security group ingress for ECS task SG, CORS configuration for Vercel origin.

### Phase 6 — DB cascade + CI/CD ✅ COMPLETE

Block 6A — DB-level FK cascade (`ON DELETE SET NULL` migration `8b9bdaf`).

Block 6B — GitHub Actions CI/CD with OIDC. No long-lived AWS keys in GitHub secrets. Workflow builds Docker image, pushes to ECR with both `latest` tag and digest, registers a new task def revision pinned to the digest, updates the service, polls `rolloutState` (replaces `wait services-stable` whose 600s cap is below real-world rollout times of ~605s).

Local Postgres aligned to 18.x to match RDS.

### Phase 7 — Observability + AI invitations ✅ COMPLETE

Block 7A — Sentry observability. Backend (`sentry-sdk[fastapi]`) and frontend (`@sentry/react`) both wired with `environment=production`. Separate Sentry projects per surface (`python-fastapi`, `javascript-react`). Verified in prod with deliberate test errors.

Block 7B — AI invitation generation. Google Gemini 2.5 Flash, native structured outputs via Pydantic `response_schema`. 5 tones (Romantic/Formal/Playful/Poetic/Simple), 3 React layouts (classic/modern/romantic) selected by AI from style description with user override. Browser print-to-PDF via portal-clone pattern. 188 tests total (+7 from designs router).

**See `## Architecture notes — AI invitation feature` below for the print-portal pattern and AI-service exception model — both are non-obvious and shouldn't be "fixed" without understanding the constraints.**

## Architecture notes — AI invitation feature

These patterns are non-obvious. Do not "simplify" without reading.

**Gemini structured outputs via Pydantic schema** — `api/services/ai_service.py` passes `GeneratedTheme` (a Pydantic model from `api/schemas/design.py`) as `response_schema` in the Gemini config. Gemini returns `response.parsed` as the Pydantic instance directly; the `_repair_json` fallback handles cases where Gemini returns text with code fences instead of native JSON.

**Auth-error matching for Gemini** — Gemini returns `400 INVALID_ARGUMENT` with `reason=API_KEY_INVALID` for bad keys, NOT `401/403` like most APIs. The exception handler matches on both status code AND message text (`API_KEY_INVALID` or `API key not valid`). Don't simplify to just `status in (401, 403)`.

**Three exception classes, one HTTP status** — `AIServiceUnconfigured` / `AIServiceUnauthorized` / `AIServiceUnavailable` all translate to HTTP 503 in `api/v1/designs.py` with distinct `detail` strings. This is for Sentry-side distinguishability without leaking config state to clients. Keep all three classes.

**`designs.html_content` stores JSON, not HTML** — the `designs` table predates the AI feature; the column name is vestigial from the Flask/WeasyPrint era. It now stores `GeneratedTheme.model_dump_json()`. Renaming would need a migration; deferred.

**Print-to-PDF uses portal clone, NOT a print stylesheet on the existing DOM** — `frontend/src/pages/designs/InvitationsPage.tsx` `handleDownloadPdf` clones `.invitation` to a `body`-level `<div class="print-portal">` before `window.print()`, then cleans up on `afterprint`. The `@media print` rule in `invitation.css` hides everything *except* `.print-portal`. Don't try to print the in-place `.invitation` — its scaled wrapper (1.2×) plus AppLayout ancestors create phantom page breaks.

**Layout selection** — Gemini picks one of `classic`/`modern`/`romantic` based on the style description (prompt-guided). User can override via dropdown. `InvitationPreview` switches the component based on `layoutOverride ?? theme.layout`. Font pairing within a layout is picked by `pickPairing()` in `fontHelpers.ts` — matches heading-font name against category lists (script/serif/sans).
