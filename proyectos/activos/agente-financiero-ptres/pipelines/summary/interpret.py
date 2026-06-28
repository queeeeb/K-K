import json

_MAX_FILAS_PROMPT = 60
_TIMEOUT_SEGUNDOS = 30


def _ask_claude_for_structure(anthropic_client, prompt: str) -> dict:
    message = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        timeout=_TIMEOUT_SEGUNDOS,
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(message.content[0].text)


def interpret_ds(rows: list[list], anthropic_client) -> dict:
    prompt = (
        "Esta es una hoja de provisiones DS. Cada mes es un bloque de 6 sub-columnas "
        "(PROVISION/NUM.FACTURA/MONTO/Diferencia+/Diferencia-/Acumulados). Identifica, para el "
        "mes más reciente presente, la columna de PROVISION, la columna de código de proyecto, "
        "y qué filas son filas de proyecto (excluye notas sueltas). "
        "Responde solo JSON con las llaves: mes_columna, provision_columna, codigo_columna, filas_proyecto.\n\n"
        f"Filas: {rows[:_MAX_FILAS_PROMPT]}"
    )
    return _ask_claude_for_structure(anthropic_client, prompt)


def interpret_engineering(rows: list[list], anthropic_client) -> dict:
    prompt = (
        "Esta es una hoja de provisiones Engineering: una columna por mes en inglés. "
        "Identifica la columna del mes más reciente, la columna de código de proyecto "
        "(formato código-cliente), y qué filas son filas de proyecto. "
        "Responde solo JSON con las llaves: mes_columna, codigo_columna, filas_proyecto.\n\n"
        f"Filas: {rows[:_MAX_FILAS_PROMPT]}"
    )
    return _ask_claude_for_structure(anthropic_client, prompt)


def interpret_consulting(rows: list[list], anthropic_client) -> dict:
    prompt = (
        "Esta es la hoja Overview Consulting. Cada proyecto ocupa un bloque de varias filas; "
        "solo la primera fila del bloque tiene STATUS/PROJECT/moneda, y el monto final es la suma "
        "de varias celdas 'Total honorarios' del bloque. El código de proyecto viene en una celda "
        "multilínea (código\\ncliente\\ndescripción). Identifica las columnas de STATUS, PROJECT, "
        "moneda y monto. Responde solo JSON con las llaves: status_columna, project_columna, "
        "moneda_columna, monto_columna.\n\n"
        f"Filas: {rows[:_MAX_FILAS_PROMPT]}"
    )
    return _ask_claude_for_structure(anthropic_client, prompt)


def interpret_facturacion(rows: list[list], anthropic_client) -> dict:
    prompt = (
        "Esta es la hoja Detalle de Facturación. El código de proyecto viene con guión "
        "(código-cliente-descripción). Identifica la columna de proyecto y la columna de estado "
        "de la factura. Responde solo JSON con las llaves: proyecto_columna, estado_columna.\n\n"
        f"Filas: {rows[:_MAX_FILAS_PROMPT]}"
    )
    return _ask_claude_for_structure(anthropic_client, prompt)
