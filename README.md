# AI Wedding Studio

A full-stack wedding planning application built with Python and Flask. Users create an account, set up a wedding profile (partner names, date, venue, style, colour palette), and manage every aspect of their event from a single dashboard — guest list and RSVPs, budget tracking, vendor contracts, a planning checklist, drag-and-drop table seating, and AI-generated theme suggestions with PDF invitation export powered by Google Gemini and WeasyPrint.

## Tech stack

**Current:** Python · Flask · SQLAlchemy · Jinja2 · Bootstrap 5 · SQLite
**Migrating to:** FastAPI · React · TypeScript (see Roadmap)

## Repository layout

```
wedding-studio/
├── backend/               # Flask application (Python 3.12, uv-managed)
│   ├── app/               # Application package
│   │   ├── routes/        # Blueprints (auth, wedding, guests, budget, …)
│   │   ├── services/      # AI, PDF, CSV, checklist, budget services
│   │   ├── static/        # CSS, JS, fonts
│   │   └── templates/     # Jinja2 templates
│   ├── migrations/        # Flask-Migrate / Alembic migrations
│   ├── config.py
│   ├── run.py
│   ├── pyproject.toml
│   └── .env.example
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
cp .env.example .env          # then open .env and set a real SECRET_KEY

# 5. Apply database migrations
flask --app run db upgrade

# 6. Start the dev server
flask --app run run --port 5001
```

Open [http://127.0.0.1:5001](http://127.0.0.1:5001).
Port 5000 is taken by AirPlay Receiver on macOS — always use 5001.

## Environment variables

See [`backend/.env.example`](backend/.env.example) for the full list with descriptions. Minimum required:

| Variable | Required | Notes |
|---|---|---|
| `SECRET_KEY` | Yes | Long random string; app warns loudly if unset |
| `FLASK_ENV` | No | `development` (default) or `production` |
| `DATABASE_URL` | No | Defaults to `sqlite:///wedding_studio.db` |
| `GEMINI_API_KEY` | No | Required only for AI theme generation |
| `DYLD_FALLBACK_LIBRARY_PATH` | macOS only | Set to `/opt/homebrew/lib` (Apple Silicon) or `/usr/local/lib` (Intel) |

## Development

```bash
# Lint + format (runs automatically on commit via pre-commit)
pre-commit run --all-files

# Run tests (pytest suite coming in Phase 5)
pytest
```

## Roadmap

- [x] **Phase 1** — Repo hygiene & tooling (monorepo layout, uv, pyproject.toml, pre-commit + Ruff + Black, Python 3.12 pin)
- [ ] **Phase 2** — Extract inline JS/CSS from Jinja templates into `static/js/` and `static/css/`
- [ ] **Phase 3** — Port backend to FastAPI with a JSON API
- [ ] **Phase 4** — Build React + TypeScript frontend
- [ ] **Phase 5** — Test coverage (pytest, Vitest, Playwright)
- [ ] **Phase 6** — Docker, CI/CD, production deployment
