import json
from unittest.mock import MagicMock

from pipelines.pl.interpret import clasificar_cuentas


def _fake_client(json_response: dict):
    client = MagicMock()
    message = MagicMock()
    message.content = [MagicMock(text=json.dumps(json_response))]
    client.messages.create.return_value = message
    return client


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
