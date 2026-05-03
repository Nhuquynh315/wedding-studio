import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.core.db import get_db
from api.main import app


@pytest.fixture
def db_engine():
    """In-memory SQLite engine with all tables created. Fresh per test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    from app import create_app

    _flask_app = create_app()
    with _flask_app.app_context():
        from app import db as _db

        _db.metadata.create_all(bind=engine)

    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """A session that gets closed after each test."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """FastAPI test client wired to the in-memory test DB."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
