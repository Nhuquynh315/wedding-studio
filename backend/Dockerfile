# ---- Stage 1: build dependencies ----
FROM python:3.12-slim AS builder

# uv: fast, reproducible installs from uv.lock
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy only dependency manifests first — layer cache means deps only
# reinstall when pyproject.toml / uv.lock change, not on every code edit.
COPY pyproject.toml uv.lock ./

# Install into a venv inside the image.
# --frozen: fail if uv.lock is out of sync with pyproject.toml.
# --no-dev: skip test/lint dependencies.
# --no-install-project: install deps only, not the app itself (we COPY
#   app code directly in stage 2).
RUN uv sync --frozen --no-dev --no-install-project

# ---- Stage 2: runtime ----
FROM python:3.12-slim AS runtime

# Non-root user — never run the app as root in a container
RUN useradd --create-home --uid 1000 appuser

WORKDIR /app

# Copy the built venv from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Put the venv on PATH so uvicorn, python etc. resolve to it
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code (respecting .dockerignore)
COPY api/ ./api/
COPY app/ ./app/
COPY migrations/ ./migrations/

# Drop to the non-root user
USER appuser

# App Runner injects PORT at runtime; default to 8000 for local runs.
# The app must bind 0.0.0.0 — inside a container, 127.0.0.1 is
# unreachable from outside.
ENV PORT=8000
EXPOSE 8000

# Shell form so ${PORT} is expanded at runtime (exec form passes it literally).
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT}
