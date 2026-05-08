# AI Wedding Studio

A full-stack wedding planning application. Users create an account, configure a wedding profile (partner names, date, venue, style, colour palette), and manage every aspect of their event from a single dashboard — guest list and RSVPs, budget tracking, vendor contracts, a planning checklist, and drag-and-drop table seating.

## Tech stack

| Layer | Tech |
|---|---|
| **API** | Python 3.12 · FastAPI · SQLAlchemy 2 · Alembic · SQLite · JWT (python-jose) |
| **Frontend** | React 18 · TypeScript · Vite · TanStack Query · React Router v7 · Tailwind CSS |
| **Testing** | pytest (171 backend tests) · Vitest · Playwright e2e |
| **Tooling** | uv · pre-commit · Ruff · Black |

## Architecture docs

- [docs/architecture.md](docs/architecture.md) — Phase 3 backend decisions (JWT, pagination, RFC 7807, test isolation)
- [docs/architecture-frontend.md](docs/architecture-frontend.md) — Phase 4 frontend decisions (state, cache invalidation, optimistic updates, form pattern)

## Repository layout

```
wedding-studio/
├── backend/               # Python application (3.12, uv-managed)
│   ├── api/               # FastAPI layer
│   │   ├── core/          # DB, deps, security, pagination, error handlers
│   │   ├── schemas/       # Pydantic schemas (Create/Update/Public per resource)
│   │   └── v1/            # Route modules (auth, weddings, guests, budget, …)
│   ├── app/               # SQLAlchemy models
│   │   └── models.py      # Shared models (imported by api/ and tests/)
│   ├── tests/             # pytest suite (171 tests, all passing)
│   ├── migrations/        # Alembic migrations
│   └── pyproject.toml
├── frontend/              # React + TypeScript SPA
│   ├── src/               # Application source
│   ├── e2e/               # Playwright end-to-end tests
│   └── package.json
├── docs/
│   ├── architecture.md
│   └── architecture-frontend.md
├── .pre-commit-config.yaml
└── CLAUDE.md
```

## Local development

### 1. Backend

```bash
cd backend
uv venv                       # creates .venv using Python 3.12 (pinned in .python-version)
source .venv/bin/activate
uv pip install -e ".[dev]"

cp .env.example .env          # then set JWT_SECRET_KEY (required)

alembic upgrade head           # create/migrate the SQLite database
uvicorn api.main:app --reload --port 8000
```

Interactive API docs: `http://127.0.0.1:8000/api/v1/docs`

### 2. Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173 — proxies /api → :8000
```

Both servers must be running for the app to work.

## API resources

| Resource | Base path | Notable features |
|---|---|---|
| Auth | `/api/v1/auth` | register, login, refresh, me |
| Weddings | `/api/v1/weddings` | CRUD; auto-seeds checklist + budget on create |
| Guests | `/api/v1/weddings/{id}/guests` | CRUD, cursor pagination, RSVP filter, bulk RSVP, CSV import |
| Budget categories | `/api/v1/weddings/{id}/budget/categories` | CRUD, proportional scale |
| Expenses | `/api/v1/weddings/{id}/budget/expenses` | CRUD |
| Budget summary | `/api/v1/weddings/{id}/budget/summary` | allocated vs. spent rollup |
| Vendors | `/api/v1/weddings/{id}/vendors` | CRUD, status filter, deposit + final payment tracking |
| Checklist | `/api/v1/weddings/{id}/checklist` | CRUD, category/priority/completed filters, bulk-complete |
| Seating tables | `/api/v1/weddings/{id}/tables` | CRUD, with-guests view (one call, full drag-and-drop state) |

All error responses use [RFC 7807](https://datatracker.ietf.org/doc/html/rfc7807) `application/problem+json`.

## Environment variables

| Variable | Required | Notes |
|---|---|---|
| `JWT_SECRET_KEY` | Yes | Signs JWT tokens — `openssl rand -hex 32` |
| `SQLALCHEMY_DATABASE_URL` | No | Defaults to `sqlite:///instance/wedding_studio.db` |
| `GEMINI_API_KEY` | No | Required only for AI theme generation |

## Running tests

```bash
# Backend — 171 tests
cd backend && source .venv/bin/activate && pytest -q

# Frontend unit tests (Vitest + Testing Library)
cd frontend && npm run test

# Frontend e2e (Playwright — auto-starts both servers)
cd frontend && npm run e2e
```

## Roadmap

- [x] **Phase 1** — Repo hygiene & tooling (uv, Ruff, Black, pre-commit, monorepo layout)
- [x] **Phase 2** — Extract inline CSS from Jinja templates
- [x] **Phase 3** — FastAPI JSON API: 9 resources, 33+ endpoints, JWT auth, RFC 7807, 171 tests
- [x] **Phase 4** — React + TypeScript SPA; removed legacy Flask/Jinja UI entirely
- [ ] **Phase 5** — Production hardening: PostgreSQL, Redis, DB-level FK cascades, token blocklist
- [ ] **Phase 6** — Docker, CI/CD, deployment
