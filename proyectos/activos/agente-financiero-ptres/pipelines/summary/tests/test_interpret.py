import json
from unittest.mock import MagicMock

from pipelines.summary.interpret import interpret_ds, interpret_engineering


def _fake_client(json_response: dict):
    client = MagicMock()
    message = MagicMock()
    message.content = [MagicMock(text=json.dumps(json_response))]
    client.messages.create.return_value = message
    return client


def test_interpret_ds_returns_structure():
    rows = [
        ["Proyecto", "Mayo PROVISION", "Mayo NUM.FACTURA"],
        ["26gmx7000.002", 5000, ""],
    ]
    fake_client = _fake_client(
        {"mes_columna": 1, "provision_columna": 1, "codigo_columna": 0, "filas_proyecto": [1]}
    )

    result = interpret_ds(rows, anthropic_client=fake_client)

    assert result["provision_columna"] == 1
    assert result["filas_proyecto"] == [1]
    fake_client.messages.create.assert_called_once()


def test_interpret_engineering_returns_structure():
    rows = [
        ["Proyecto", "Jan", "Feb", "Mar", "Apr", "May"],
        ["26gmx2000.005-Cliente Cuatro", 0, 0, 0, 0, 3000],
    ]
    fake_client = _fake_client({"mes_columna": 5, "codigo_columna": 0, "filas_proyecto": [1]})

    result = interpret_engineering(rows, anthropic_client=fake_client)

    assert result["mes_columna"] == 5
    assert result["filas_proyecto"] == [1]
