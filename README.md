# AI Wedding Studio

A full-stack wedding planning application built with Python and Flask, currently being ported to FastAPI + React. Users create an account, set up a wedding profile (partner names, date, venue, style, colour palette), and manage every aspect of their event from a single dashboard — guest list and RSVPs, budget tracking, vendor contracts, a planning checklist, drag-and-drop table seating, and AI-generated theme suggestions with PDF invitation export powered by Google Gemini and WeasyPrint.

## Tech stack

**Backend (stable):** Python · FastAPI · SQLAlchemy · SQLite · JWT auth
**Legacy UI (still running):** Flask · Jinja2 · Bootstrap 5
**Migrating to:** React · TypeScript · Vite (Phase 4)

## Repository layout

```
wedding-studio/
├── backend/               # Python application (3.12, uv-managed)
│   ├── api/               # FastAPI layer
│   │   ├── core/          # DB, deps, security, pagination, error handlers
│   │   ├── schemas/       # Pydantic schemas (Create/Update/Public per resource)
│   │   └── v1/            # Route modules (auth, weddings, guests, budget, …)
│   ├── app/               # Flask/SQLAlchemy models + legacy Jinja routes
│   │   ├── models.py      # Shared SQLAlchemy models (read by both layers)
│   │   ├── routes/        # Legacy blueprints (still served during Phase 4 build)
│   │   └── services/      # AI, PDF, CSV, checklist, budget services
│   ├── tests/             # pytest suite (171 tests, all passing)
│   ├── migrations/        # Flask-Migrate / Alembic migrations
│   └── pyproject.toml
├── docs/
│   └── architecture.md    # Phase 3 architecture decisions
├── frontend/              # (coming — React + TypeScript, Phase 4)
├── .pre-commit-config.yaml
└── CLAUDE.md
```

## Prerequisites

- **Python 3.12** via [uv](https://github.com/astral-sh/uv)
- **uv** — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **macOS only:** Pango/Cairo system libraries for WeasyPrint PDF export
  ```bash
  brew install pango cairo glib
  ```

## Setup

```bash
# 1. Clone
git clone <repo-url>
cd wedding-studio

# 2. Install pre-commit hooks
pre-commit install

# 3. Create venv and install dependencies
cd backend
uv venv                       # uses Python 3.12 from .python-version
source .venv/bin/activate
uv pip install -e ".[dev]"

# 4. Configure environment
cp .env.example .env          # then open .env and set SECRET_KEY + JWT_SECRET_KEY

# 5. Apply database migrations
flask --app run db upgrade

# 6. Start the legacy Flask server (for the Jinja UI)
flask --app run run --port 5001
```

Open [http://127.0.0.1:5001](http://127.0.0.1:5001).
Port 5000 is taken by AirPlay Receiver on macOS — always use 5001.

## API (Phase 3 — complete)

```bash
# Run the FastAPI server
cd backend
source .venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

Interactive docs at [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs).

### Resources

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

### Running tests

```bash
cd backend
source .venv/bin/activate
pytest -v          # 171 tests, ~80s
```

## Environment variables

See [`backend/.env.example`](backend/.env.example) for the full list. Minimum required:

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | Yes | Flask secret; long random string |
| `JWT_SECRET_KEY` | Yes | Signs JWT tokens; `openssl rand -hex 32` |
| `FLASK_ENV` | No | `development` (default) or `production` |
| `DATABASE_URL` | No | Defaults to `sqlite:///wedding_studio.db` |
| `SQLALCHEMY_DATABASE_URL` | No | Defaults to same SQLite path (for FastAPI layer) |
| `GEMINI_API_KEY` | No | Required only for AI theme generation |
| `DYLD_FALLBACK_LIBRARY_PATH` | macOS only | `/opt/homebrew/lib` (Apple Silicon) or `/usr/local/lib` (Intel) |

## Development

```bash
# Lint + format (runs automatically on commit via pre-commit)
pre-commit run --all-files

# Run tests
cd backend && pytest -v
```

## Roadmap

- [x] **Phase 1** — Repo hygiene & tooling (monorepo layout, uv, pyproject.toml, pre-commit + Ruff + Black, Python 3.12 pin)
- [x] **Phase 2** — Extract inline CSS from `base.html` and `dashboard.html`
- [x] **Phase 3** — FastAPI JSON API: 7 resources, 33 endpoints, JWT auth, RFC 7807 errors, 171 tests
- [ ] **Phase 4** — React + TypeScript frontend (replaces Jinja templates)
- [ ] **Phase 5** — Production hardening: PostgreSQL, Redis, DB-level FK cascades, token blocklist
- [ ] **Phase 6** — Docker, CI/CD, deployment
