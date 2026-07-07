import json
from pathlib import Path
from unittest.mock import MagicMock

from pipelines.summary.orquestador import interpretar_summary

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _fake_client_con_respuestas(respuestas: list[dict]):
    client = MagicMock()
    mensajes = []
    for r in respuestas:
        m = MagicMock()
        m.content = [MagicMock(text=json.dumps(r))]
        mensajes.append(m)
    client.messages.create.side_effect = mensajes
    return client


def test_interpretar_summary_combina_las_4_fuentes():
    raw_files = {
        "base": str(FIXTURES_DIR / "summary_abril.xlsm"),
        "facturacion": str(FIXTURES_DIR / "facturacion_mayo.xlsx"),
        "ds": str(FIXTURES_DIR / "provisiones_ds_mayo.xlsx"),
        "engineering": str(FIXTURES_DIR / "provisiones_engineering_mayo.xlsx"),
        "consulting": str(FIXTURES_DIR / "overview_consulting_mayo.xlsx"),
    }
    # orden de llamadas: facturacion, ds, engineering, consulting
    client = _fake_client_con_respuestas([
        {"proyecto_columna": 0, "estado_columna": 1, "periodo_columna": 2},
        {"provision_columna": 1, "codigo_columna": 0, "cliente_columna": 6, "nombre_columna": 7, "fila_inicio_datos": 2},
        {"mes_columna": 5, "codigo_columna": 0, "nombre_columna": 6, "fila_inicio_datos": 1},
        {"status_columna": 0, "project_columna": 1, "trigger_columna": 2, "monto_columna": 3},
    ])

    resultado = interpretar_summary(raw_files, client, mes="2026-05")

    assert resultado["ledger_vivo"] == [
        {"proyecto": "26gmx3000.001", "monto_mxn": 17950, "cc": 3000, "cliente": "Cliente Uno",
         "nombre_proyecto": "Proyecto Uno", "moneda": "USD", "monto_original": 1000, "tc": 17.95,
         "anio": 2026, "periodo": "Abril"},
        {"proyecto": "26gmx7000.002", "monto_mxn": 5000, "cc": 7000, "cliente": "Cliente Dos",
         "nombre_proyecto": "Proyecto Dos", "moneda": "MXN", "monto_original": 5000, "tc": 1,
         "anio": 2026, "periodo": "Abril"},
    ]
    assert resultado["ruta_base"] == raw_files["base"]
    assert resultado["hoja_mes_anterior"] == "2026_Abr"
    assert resultado["hoja_mes_nuevo"] == "2026_May"

    # solo la factura Pagado genera cierre (la Cancelado se ignora), por periodo Abril
    assert resultado["cierres"] == [
        {"codigo": "26gmx3000.001", "anio": 2026, "mes": "Abril", "origen": "facturacion"},
    ]
    assert resultado["concentrado"][3000] == {"facturado": 1000, "canceladas": 100}

    proyectos_actuales = {p["proyecto"] for p in resultado["provisiones_actuales"]}
    assert proyectos_actuales == {"26gmx7000.002", "26gmx2000.005", "26gmx3000.001"}

    assert "26gmx3000.001" in resultado["codigos_conocidos"]
    assert "26gmx7000.002" in resultado["codigos_conocidos"]


def test_separar_sospechosos_acepta_consecutivo_odoo_con_o_sin_espacio():
    from pipelines.summary.orquestador import _separar_sospechosos

    provisiones = [
        {"proyecto": "26gmx3000.001", "monto_mxn": 1000, "cc": 3000, "cliente": "Cliente Uno"},
        {"proyecto": "26gmx7000. S02968", "monto_mxn": 500, "cc": 7000, "cliente": ""},
        {"proyecto": "25gmx7000.S02393", "monto_mxn": 700, "cc": 7000, "cliente": ""},
    ]

    validas, alertas = _separar_sospechosos(provisiones)

    assert {p["proyecto"] for p in validas} == {
        "26gmx3000.001", "26gmx7000. S02968", "25gmx7000.S02393",
    }
    assert alertas == []


def test_separar_sospechosos_excluye_codigos_sin_estructura_gmx_y_alerta():
    from pipelines.summary.orquestador import _separar_sospechosos

    provisiones = [
        {"proyecto": "26gmx3000.001", "monto_mxn": 1000, "cc": 3000, "cliente": "Cliente Uno"},
        {"proyecto": "Se facturó junto con Abril", "monto_mxn": 500, "cc": None, "cliente": ""},
    ]

    validas, alertas = _separar_sospechosos(provisiones)

    assert [p["proyecto"] for p in validas] == ["26gmx3000.001"]
    assert len(alertas) == 1
    assert "Se facturó junto con Abril" in alertas[0]


def test_interpretar_summary_reporta_alertas_de_codigos_sospechosos():
    raw_files = {
        "base": str(FIXTURES_DIR / "summary_abril.xlsm"),
        "facturacion": str(FIXTURES_DIR / "facturacion_mayo.xlsx"),
        "ds": str(FIXTURES_DIR / "provisiones_ds_mayo.xlsx"),
        "engineering": str(FIXTURES_DIR / "provisiones_engineering_mayo.xlsx"),
        "consulting": str(FIXTURES_DIR / "overview_consulting_mayo.xlsx"),
    }
    client = _fake_client_con_respuestas([
        {"proyecto_columna": 0, "estado_columna": 1, "periodo_columna": 2},
        {"provision_columna": 1, "codigo_columna": 0, "cliente_columna": 6, "nombre_columna": 7, "fila_inicio_datos": 2},
        {"mes_columna": 5, "codigo_columna": 0, "nombre_columna": 6, "fila_inicio_datos": 1},
        {"status_columna": 0, "project_columna": 1, "trigger_columna": 2, "monto_columna": 3},
    ])

    resultado = interpretar_summary(raw_files, client, mes="2026-05")

    assert not any("sospechoso" in a.lower() for a in resultado["alertas"])
    proyectos = {p["proyecto"] for p in resultado["provisiones_actuales"]}
    assert "26gmx7000.002" in proyectos
