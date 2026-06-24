import json
from unittest.mock import MagicMock

from pipelines.pl.interpret import clasificar_cuentas, interpret_estructura


def _fake_client(json_response: dict):
    client = MagicMock()
    message = MagicMock()
    message.content = [MagicMock(text=json.dumps(json_response))]
    client.messages.create.return_value = message
    return client


def test_interpret_estructura_devuelve_tipos_de_fila():
    rows = [
        ["P-TRES GROUP, S.A.P.I. DE C.V."],
        [""],
        ["Del 1 al 31 de Marzo 2026"],
        ["4110-002-001-000", "FORD MOTOR COMPANY"],
        ["Segmento: 2000 ING"],
        ["", "", "", "", "Total Seg. ENGINEERING", 0, 1000],
    ]
    fake = _fake_client(
        {
            "periodo": "Marzo 2026",
            "columnas": {"cuenta": 1, "nombre": 2, "cargos": 6, "abonos": 7},
            "filas_cuenta": [4],
            "filas_segmento": [5],
            "filas_total_segmento": [6],
            "filas_diario": [],
        }
    )

    result = interpret_estructura(rows, anthropic_client=fake)

    assert result["periodo"] == "Marzo 2026"
    assert result["filas_total_segmento"] == [6]
    fake.messages.create.assert_called_once()


def test_clasificar_cuentas_marca_nuevo():
    cuentas = [
        {"numero": "6100-007-099-000", "nombre": "SUSCRIPCION NUEVA SaaS"},
    ]
    fake = _fake_client(
        {
            "cuentas": [
                {
                    "numero": "6100-007-099-000",
                    "grupo": "6007",
                    "rubro": "EXPENSES",
                    "label_en": "  NEW SAAS SUBSCRIPTION",
                    "nuevo": True,
                }
            ]
        }
    )

    result = clasificar_cuentas(cuentas, anthropic_client=fake)

    assert result["cuentas"][0]["rubro"] == "EXPENSES"
    assert result["cuentas"][0]["nuevo"] is True
