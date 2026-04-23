# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

Environment variables are loaded from `.env`. Minimum required:
```
FLASK_ENV=development
SECRET_KEY=<any string>
DATABASE_URL=sqlite:///wedding_studio.db   # optional, this is the default
GEMINI_API_KEY=<key>                       # required for AI theme generation
```

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
| `budget_service.py` | Implemented | Seeds a new wedding with 8 default budget categories based on a $20k reference budget |

**Templates** extend `base.html` using `{% block content %}`, `{% block extra_css %}`, `{% block extra_js %}`. Wedding templates live in `app/templates/wedding/`. Auth templates in `app/templates/auth/`. Error templates in `app/templates/errors/`. Brand CSS variables (rose palette) defined under `:root` in `app/static/css/style.css`, loaded globally by `base.html`.

**Fonts:** Lora (headings) and DM Sans (body/UI) loaded via Google Fonts in `base.html`. Self-hosted fallback for Playfair Display is in `app/static/fonts/`.

**Database**: SQLite in development (`instance/wedding_studio.db`). Schema is managed exclusively by Flask-Migrate — `db.create_all()` has been removed. Run `flask db upgrade` on first setup and after every model change.

## Known refactor opportunities

**Authorization-check-and-discard pattern (Phase 3):** Six routes call `get_wedding_or_403(wedding_id)` purely for its 403-raising side effect without using the returned `Wedding` object (`budget.py`, `checklist.py`, `seating.py` ×3, `vendors.py`). These should be consolidated into a decorator (e.g. `@require_wedding_ownership`) in Phase 3 when the route layer is refactored.

## Active refactor — Phase 1

The following structural changes are in progress or planned:

**(a) Move Flask app into `backend/`**
Reorganise the repo so the Flask application lives under `backend/` with its own `config.py`, `run.py`, and `app/` package. The repo root will hold only top-level config files and the future frontend workspace.

**(b) Migrate from `requirements.txt` to `pyproject.toml` with uv**
Replace the current `requirements.txt`-based dependency management with a `pyproject.toml` managed by [uv](https://github.com/astral-sh/uv). The existing `venv/` will be replaced by a uv-managed virtual environment.

**(c) Add pre-commit with Ruff and Black**
Introduce a `.pre-commit-config.yaml` running Ruff (lint + import sort) and Black (format) on every commit. CI will enforce the same checks.

**(d) Future FastAPI + React/TypeScript split**
The longer-term goal is to replace the Jinja2 frontend with a React/TypeScript SPA and migrate the backend from Flask to FastAPI. Phase 1 lays the groundwork (monorepo structure, tooling) without breaking the current Flask app.
