import json

_MAX_FILAS_PROMPT = 15
_TIMEOUT_SEGUNDOS = 30
_INSTRUCCION_INDICE = (
    "IMPORTANTE: cada *_columna debe ser el índice numérico de la columna (0 = primera posición "
    "de la fila), nunca el nombre del encabezado. Responde ÚNICAMENTE el JSON, sin explicación "
    "antes ni después."
)


def _enmascarar_montos(rows: list[list]) -> list[list]:
    return [
        ["#" if isinstance(cell, (int, float)) and not isinstance(cell, bool) else cell for cell in row]
        for row in rows
    ]


def _extraer_json(text: str) -> str:
    text = text.strip()
    if "```" in text:
        for parte in text.split("```"):
            parte = parte.strip()
            if parte.startswith("json"):
                parte = parte[len("json"):].strip()
            if parte.startswith("{"):
                return parte
    inicio, fin = text.find("{"), text.rfind("}")
    if inicio != -1 and fin != -1:
        return text[inicio:fin + 1]
    return text


def _ask_claude_for_structure(anthropic_client, prompt: str) -> dict:
    message = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        timeout=_TIMEOUT_SEGUNDOS,
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(_extraer_json(message.content[0].text))


def interpret_ds(rows: list[list], anthropic_client) -> dict:
    filas = _enmascarar_montos(rows[:_MAX_FILAS_PROMPT])
    prompt = (
        "Esta es una hoja de provisiones DS. Cada mes es un bloque de 6 sub-columnas "
        "(PROVISION/NUM.FACTURA/MONTO/Diferencia+/Diferencia-/Acumulados). Los montos se muestran "
        "como '#' — identifica la estructura por posición y encabezados, no por valores. Identifica, "
        "para el mes más reciente presente, la columna de PROVISION, la columna de código de "
        "proyecto, y en qué fila (índice) empiezan los datos de proyecto (después de encabezados). "
        "Responde solo JSON con las llaves: mes_columna, provision_columna, codigo_columna, fila_inicio_datos. "
        f"{_INSTRUCCION_INDICE}\n\n"
        f"Filas: {filas}"
    )
    return _ask_claude_for_structure(anthropic_client, prompt)


def interpret_engineering(rows: list[list], anthropic_client) -> dict:
    filas = _enmascarar_montos(rows[:_MAX_FILAS_PROMPT])
    prompt = (
        "Esta es una hoja de provisiones Engineering: una columna por mes en inglés. Los montos se "
        "muestran como '#' — identifica la estructura por posición y encabezados, no por valores. "
        "Identifica la columna del mes más reciente, la columna de código de proyecto "
        "(formato código-cliente), y en qué fila (índice) empiezan los datos de proyecto. "
        "Responde solo JSON con las llaves: mes_columna, codigo_columna, fila_inicio_datos. "
        f"{_INSTRUCCION_INDICE}\n\n"
        f"Filas: {filas}"
    )
    return _ask_claude_for_structure(anthropic_client, prompt)


def interpret_consulting(rows: list[list], anthropic_client) -> dict:
    filas = _enmascarar_montos(rows[:_MAX_FILAS_PROMPT])
    prompt = (
        "Esta es la hoja Overview Consulting. Cada proyecto ocupa un bloque de varias filas; "
        "solo la primera fila del bloque tiene STATUS/PROJECT. Dentro del bloque, una o más filas "
        "tienen el texto literal 'Total honorarios' en una columna (la 'columna disparador') — el "
        "monto real de ESA fila (en otra columna, la 'columna de monto') es el que se debe sumar. "
        "Si hay varias filas con 'Total honorarios' en el mismo bloque (ej. por moneda distinta), "
        "se suman todas. El código de proyecto viene en una celda multilínea "
        "(código\\ncliente\\ndescripción). Identifica las columnas de STATUS, PROJECT, la columna "
        "disparador (donde aparece el texto 'Total honorarios') y la columna de monto. "
        "Responde solo JSON con las llaves: status_columna, project_columna, "
        "trigger_columna, monto_columna. "
        f"{_INSTRUCCION_INDICE}\n\n"
        f"Filas: {filas}"
    )
    return _ask_claude_for_structure(anthropic_client, prompt)


def interpret_facturacion(rows: list[list], anthropic_client) -> dict:
    filas = _enmascarar_montos(rows[:_MAX_FILAS_PROMPT])
    prompt = (
        "Esta es la hoja Detalle de Facturación. El código de proyecto viene con guión "
        "(código-cliente-descripción). Identifica la columna de proyecto y la columna de estado "
        "de la factura. Responde solo JSON con las llaves: proyecto_columna, estado_columna. "
        f"{_INSTRUCCION_INDICE}\n\n"
        f"Filas: {filas}"
    )
    return _ask_claude_for_structure(anthropic_client, prompt)
