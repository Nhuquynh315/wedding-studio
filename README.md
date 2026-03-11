# AI Wedding Studio

A web application for planning and managing weddings. Users can create an account, build wedding profiles with partner names, date, venue, style, and colour palette, and manage their weddings from a personal dashboard. The project is designed to eventually integrate AI-generated themes and PDF invitation exports.

## Tech Stack

- **Backend:** Python, Flask, SQLAlchemy, Flask-Login, Flask-Migrate, Flask-WTF, Flask-Limiter
- **Database:** SQLite (development) — configurable via `DATABASE_URL`
- **Frontend:** Jinja2 templates, Bootstrap 5

## Running Locally

```bash
# 1. Clone the repo
git clone <repo-url>
cd wedding-studio

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env            # or create .env manually
# Edit .env and set a SECRET_KEY

# 5. Apply database migrations
flask db upgrade

# 6. Start the development server
flask run --port 5001
```

> **macOS note:** Port 5000 is used by AirPlay Receiver. Use `--port 5001` or disable AirPlay Receiver in System Settings → General → AirDrop & Handoff.

Then open [http://127.0.0.1:5001](http://127.0.0.1:5001) in your browser.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Flask session signing key — use a long random string in production |
| `DATABASE_URL` | No | Defaults to `sqlite:///wedding_studio.db` |
| `FLASK_ENV` | No | Set to `development` to enable debug mode |
