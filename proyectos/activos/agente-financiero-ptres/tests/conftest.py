import pytest
from fastapi.testclient import TestClient

from core import auth
from core.api import _conn, app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers(monkeypatch):
    monkeypatch.setenv("AGENTE_JWT_SECRET", "secreto-de-prueba-no-real-32bytes!!")

    def _headers_for(username: str, password: str = "clave123") -> dict[str, str]:
        conn = _conn()
        auth.crear_usuario(conn, username, password)
        token = auth.create_access_token(username)
        return {"Authorization": f"Bearer {token}"}

    return _headers_for
