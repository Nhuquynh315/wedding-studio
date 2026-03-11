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

# Install dependencies
pip install -r requirements.txt
```

Environment variables are loaded from `.env`. Minimum required:
```
FLASK_ENV=development
SECRET_KEY=<any string>
DATABASE_URL=sqlite:///wedding_studio.db   # optional, this is the default
```

## Architecture

**Application factory** in `app/__init__.py` — `create_app(config_name)` accepts `'development'`, `'testing'`, or `'production'`. Config classes live in `config.py`. Extensions initialised at module level: `db`, `login_manager`, `migrate`, `csrf`, `limiter`.

**Blueprint layout:**
| Blueprint | File | Notes |
|---|---|---|
| `main_bp` | `app/routes/main.py` | Home page only |
| `auth_bp` | `app/routes/auth.py` | Register, login, logout |
| `wedding_bp` | `app/routes/wedding.py` | Dashboard, create wedding |
| `guests_bp` | `app/routes/guests.py` | Empty — not yet implemented |

All blueprints are re-exported through `app/routes/__init__.py`.

**Models** (`app/models.py`): `User`, `Wedding`, `Guest`, `Design`. Relationships use `cascade='all, delete-orphan'`. `WEDDING_STYLES` tuple defines valid style values — always validate `style` against it. Always filter `Wedding` queries by `user_id=current_user.id` (ownership).

**Security layer:**
- `CSRFProtect` — active globally; every form needs `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`. CSRF error renders `app/templates/errors/csrf.html`.
- `Flask-Limiter` — `limiter` exported from `app/__init__.py`; applied per-route with `@limiter.limit(...)`.
- `db.session.commit()` calls are wrapped in `try/except` with `db.session.rollback()` on failure.

**Service layer** (`app/services/`): `ai_service.py`, `pdf_service.py`, `csv_service.py` — all empty placeholders.

**Templates** extend `base.html` using `{% block content %}`, `{% block extra_css %}`, `{% block extra_js %}`. Wedding templates live in `app/templates/wedding/`. Auth templates in `app/templates/auth/`. Error templates in `app/templates/errors/`. Brand CSS variables (rose palette) defined under `:root` in `app/static/css/style.css`, loaded globally by `base.html`.

**Database**: SQLite in development (`instance/wedding_studio.db`). Schema is managed exclusively by Flask-Migrate — `db.create_all()` has been removed. Run `flask db upgrade` on first setup and after every model change.
