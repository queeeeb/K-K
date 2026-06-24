import pytest
from fastapi.testclient import TestClient

from core.api import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
