import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client — usable in any test that needs to hit the API."""
    return TestClient(app)
