# AI Wedding Studio

A full-stack wedding planning application built with Python (FastAPI) and React. Users create an account, set up a wedding profile (partner names, date, venue, style, colour palette), and manage every aspect of their event from a single dashboard — guest list and RSVPs, budget tracking, vendor contracts, a planning checklist, and drag-and-drop table seating.

## Tech stack

**Backend:** Python · FastAPI · SQLAlchemy · SQLite · JWT auth
**Frontend:** React · TypeScript · Vite · TanStack Query · Tailwind CSS

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
│   ├── src/
│   ├── e2e/               # Playwright end-to-end tests
│   └── package.json
├── docs/
│   └── architecture.md    # Phase 3 architecture decisions
├── .pre-commit-config.yaml
└── CLAUDE.md
```

## Setup

### Backend

```bash
cd backend
uv venv                       # uses Python 3.12 from .python-version
source .venv/bin/activate
uv pip install -e ".[dev]"

# Configure environment
cp .env.example .env          # set JWT_SECRET_KEY (required)

# Apply database migrations
alembic upgrade head

# Start the API server
uvicorn api.main:app --reload --port 8000
```

Interactive docs at [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs).

### Frontend

```bash
cd frontend
npm install
npm run dev          # starts on http://localhost:5173 (proxies /api to :8000)
```

## API resources

| Resource | Base path | Endpoints |
|---|---|---|
| Auth | `/api/v1/auth` | register, login, refresh, me |
| Weddings | `/api/v1/weddings` | CRUD |
| Guests | `/api/v1/weddings/{id}/guests` | CRUD, cursor pagination, RSVP filter, bulk RSVP, CSV import |
| Budget categories | `/api/v1/weddings/{id}/budget/categories` | CRUD, scale |
| Expenses | `/api/v1/weddings/{id}/budget/expenses` | CRUD |
| Budget summary | `/api/v1/weddings/{id}/budget/summary` | GET |
| Vendors | `/api/v1/weddings/{id}/vendors` | CRUD, status filter |
| Checklist | `/api/v1/weddings/{id}/checklist` | CRUD, category/priority/completed filters, bulk-complete |
| Seating tables | `/api/v1/weddings/{id}/tables` | CRUD, with-guests view |

All error responses use [RFC 7807](https://datatracker.ietf.org/doc/html/rfc7807) `application/problem+json`.

## Environment variables

| Variable | Required | Notes |
|---|---|---|
| `JWT_SECRET_KEY` | Yes | Signs JWT tokens; `openssl rand -hex 32` |
| `SQLALCHEMY_DATABASE_URL` | No | Defaults to `sqlite:///instance/wedding_studio.db` |
| `GEMINI_API_KEY` | No | Required only for AI theme generation |

## Running tests

```bash
# Backend (pytest)
cd backend && source .venv/bin/activate && pytest -v

# Frontend unit tests (Vitest)
cd frontend && npm run test

# Frontend e2e (Playwright — starts backend + dev server automatically)
cd frontend && npm run e2e
```

## Roadmap

- [x] **Phase 1** — Repo hygiene & tooling
- [x] **Phase 2** — Extract inline CSS from Jinja templates
- [x] **Phase 3** — FastAPI JSON API: 7 resources, 33 endpoints, JWT auth, RFC 7807 errors, 171 tests
- [x] **Phase 4** — React + TypeScript frontend; removed legacy Flask UI
- [ ] **Phase 5** — Production hardening: PostgreSQL, Redis, DB-level FK cascades, token blocklist
- [ ] **Phase 6** — Docker, CI/CD, deployment
