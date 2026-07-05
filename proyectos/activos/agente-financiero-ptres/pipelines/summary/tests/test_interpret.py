import json
from unittest.mock import MagicMock

from pipelines.summary.interpret import _enmascarar_montos, interpret_ds, interpret_engineering


def _fake_client(json_response: dict):
    client = MagicMock()
    message = MagicMock()
    message.content = [MagicMock(text=json.dumps(json_response))]
    client.messages.create.return_value = message
    return client


def test_enmascarar_montos_reemplaza_numeros_y_conserva_texto():
    rows = [
        ["Proyecto", "Mayo PROVISION"],
        ["26gmx7000.002", 47832.19],
        ["Nota suelta sin código", None],
    ]

    resultado = _enmascarar_montos(rows)

    assert resultado[0] == ["Proyecto", "Mayo PROVISION"]
    assert resultado[1] == ["26gmx7000.002", "#"]
    assert resultado[2] == ["Nota suelta sin código", None]


def test_ask_claude_for_structure_ignora_prosa_antes_del_json():
    from pipelines.summary.interpret import _ask_claude_for_structure

    client = MagicMock()
    message = MagicMock()
    message.content = [MagicMock(text=(
        'Looking at the data, the most recent month is Junio.\n\n'
        '```json\n{"mes_columna": 36, "codigo_columna": 3}\n```'
    ))]
    client.messages.create.return_value = message

    resultado = _ask_claude_for_structure(client, "prompt")

    assert resultado == {"mes_columna": 36, "codigo_columna": 3}


def test_ask_claude_for_structure_quita_markdown_code_fence():
    from pipelines.summary.interpret import _ask_claude_for_structure

    client = MagicMock()
    message = MagicMock()
    message.content = [MagicMock(text='```json\n{"mes_columna": 1}\n```')]
    client.messages.create.return_value = message

    resultado = _ask_claude_for_structure(client, "prompt")

    assert resultado == {"mes_columna": 1}


def test_interpret_ds_returns_structure():
    rows = [
        ["Proyecto", "Mayo PROVISION", "Mayo NUM.FACTURA"],
        ["26gmx7000.002", 5000, ""],
    ]
    fake_client = _fake_client(
        {"mes_columna": 1, "provision_columna": 1, "codigo_columna": 0, "fila_inicio_datos": 1}
    )

    result = interpret_ds(rows, anthropic_client=fake_client)

    assert result["provision_columna"] == 1
    assert result["fila_inicio_datos"] == 1
    fake_client.messages.create.assert_called_once()


def test_interpret_ds_no_manda_monto_real_al_prompt():
    rows = [
        ["Proyecto", "Mayo PROVISION", "Mayo NUM.FACTURA"],
        ["26gmx7000.002", 47832.19, ""],
    ]
    fake_client = _fake_client(
        {"mes_columna": 1, "provision_columna": 1, "codigo_columna": 0, "fila_inicio_datos": 1}
    )

    interpret_ds(rows, anthropic_client=fake_client)

    prompt_enviado = fake_client.messages.create.call_args.kwargs["messages"][0]["content"]
    assert "47832.19" not in prompt_enviado
    assert "26gmx7000.002" in prompt_enviado


def test_interpret_engineering_returns_structure():
    rows = [
        ["Proyecto", "Jan", "Feb", "Mar", "Apr", "May"],
        ["26gmx2000.005-Cliente Cuatro", 0, 0, 0, 0, 3000],
    ]
    fake_client = _fake_client({"mes_columna": 5, "codigo_columna": 0, "fila_inicio_datos": 1})

    result = interpret_engineering(rows, anthropic_client=fake_client)

    assert result["mes_columna"] == 5
    assert result["fila_inicio_datos"] == 1
