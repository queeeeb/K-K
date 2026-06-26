from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook

from core import auth
from core.api import _conn, app
from core.registry import clear_registry, register
from pipelines.summary.spec import build_summary_spec

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENTE_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("AGENTE_JWT_SECRET", "secreto-de-prueba-no-real-32bytes!!")
    clear_registry()

    destino = tmp_path / "summary_mayo.xlsm"

    def fake_interpret(raw_files):
        return {
            "provisiones_mes_anterior": [
                {"proyecto": "26gmx3000.001", "monto_mxn": 1000, "cc": 3000, "cliente": "Cliente Uno"},
                {"proyecto": "26gmx4000.001", "monto_mxn": 2000, "cc": 4000, "cliente": "Cliente Dos"},
            ],
            "facturas_mes": [
                {"proyecto": "26gmx3000.001-Cliente Uno- Proyecto Uno", "estado": "Pagado"}
            ],
            "provisiones_nuevas": [
                {"proyecto": "26gmx2000.005", "monto_mxn": 3000, "cc": 2000, "cliente": "Cliente Cuatro"}
            ],
        }

    spec = build_summary_spec(
        interpret_override=fake_interpret,
        ruta_origen=str(FIXTURES_DIR / "summary_abril.xlsm"),
        ruta_destino=str(destino),
        hoja_mes_anterior="2026_Abr",
        hoja_mes_nuevo="2026_May",
    )
    register(spec)
    conn = _conn()
    auth.crear_usuario(conn, "luis", "clave123")
    token = auth.create_access_token("luis")
    headers = {"Authorization": f"Bearer {token}"}
    yield TestClient(app), destino, headers
    clear_registry()


def test_procesar_confirmar_escribe_archivo(client):
    test_client, destino, headers = client

    procesar = test_client.post("/procesar/summary", json={"mes": "2026_May"}, headers=headers)
    assert procesar.status_code == 200
    resumen = procesar.json()["resumen"]
    assert len(resumen["canceladas"]) == 1
    assert len(resumen["nuevas"]) == 1
    assert "alertas" in resumen
    assert resumen["activas"][0]["monto_mxn_anterior"] == resumen["activas"][0]["monto_mxn"]

    confirmar = test_client.post("/confirmar/summary", json={"token": procesar.json()["token"]}, headers=headers)
    assert confirmar.status_code == 200
    reporte = confirmar.json()["reporte"]
    assert reporte["canceladas"] == 1
    assert reporte["nuevas"] == 1
    assert "filas_escritas" in reporte

    wb = load_workbook(destino)
    hoja = wb["2026_May"]
    assert hoja.cell(row=14, column=8).value == "26gmx2000.005"
    for row in range(1, 12):
        assert hoja.cell(row=row, column=1).value == f"KPI fila {row}"
