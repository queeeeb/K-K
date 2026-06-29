import pytest

from core.pipeline_spec import PipelineSpec
from core.registry import clear_registry, register


@pytest.fixture(autouse=True)
def fake_pipeline(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTE_DB_PATH", str(tmp_path / "test.db"))
    clear_registry()

    def fake_interpret(raw_files):
        return {"raw": raw_files}

    def fake_calculate(estructura, estado_anterior):
        return {
            "resumen": {"nuevas": [{"proyecto": "X-1", "monto_mxn": 100}]},
            "detalle": {"filas": [{"proyecto": "X-1", "monto_mxn": 100}]},
        }

    def fake_write(plan_detalle, archivo_destino):
        return {"archivo": "fake.xlsm", "filas_escritas": len(plan_detalle["filas"])}

    register(
        PipelineSpec(
            name="fake", sources=["fuente.xlsx"], interpret=fake_interpret,
            calculate=fake_calculate, write=fake_write,
        )
    )
    yield
    clear_registry()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_con_credenciales_correctas_devuelve_token(client, auth_headers):
    auth_headers("luis")
    response = client.post("/login", json={"usuario": "luis", "password": "clave123"})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 8 * 3600
    assert "access_token" in body


def test_login_con_password_incorrecto_devuelve_401(client, auth_headers):
    auth_headers("luis")
    response = client.post("/login", json={"usuario": "luis", "password": "clave-equivocada"})

    assert response.status_code == 401


def test_procesar_sin_token_devuelve_401(client):
    response = client.post("/procesar/fake", data={"mes": "2026_May"})
    assert response.status_code == 401


def test_procesar_then_confirmar(client, auth_headers):
    headers = auth_headers("luis")

    response = client.post("/procesar/fake", data={"mes": "2026_May"}, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert "token" in body
    assert body["resumen"]["nuevas"][0]["proyecto"] == "X-1"

    response = client.post("/confirmar/fake", json={"token": body["token"]}, headers=headers)
    assert response.status_code == 200
    assert response.json()["reporte"]["filas_escritas"] == 1


def test_procesar_locked_returns_409(client, auth_headers):
    headers_luis = auth_headers("luis")
    headers_oswaldo = auth_headers("oswaldo")

    first = client.post("/procesar/fake", data={"mes": "2026_May"}, headers=headers_luis)
    assert first.status_code == 200

    second = client.post("/procesar/fake", data={"mes": "2026_May"}, headers=headers_oswaldo)
    assert second.status_code == 409
    assert "luis" in second.json()["detail"]


def test_rechazar_frees_lock(client, auth_headers):
    headers_luis = auth_headers("luis")
    headers_oswaldo = auth_headers("oswaldo")

    first = client.post("/procesar/fake", data={"mes": "2026_May"}, headers=headers_luis)
    token = first.json()["token"]

    rechazar = client.post("/rechazar/fake", json={"token": token}, headers=headers_luis)
    assert rechazar.status_code == 200

    second = client.post("/procesar/fake", data={"mes": "2026_May"}, headers=headers_oswaldo)
    assert second.status_code == 200
