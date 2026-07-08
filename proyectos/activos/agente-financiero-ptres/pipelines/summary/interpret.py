import json

from pipelines.summary.periodos import normalizar_periodo

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


_MESES_NUMERO = {
    1: "enero/January/Jan", 2: "febrero/February/Feb", 3: "marzo/March/Mar",
    4: "abril/April/Apr", 5: "mayo/May", 6: "junio/June/Jun", 7: "julio/July/Jul",
    8: "agosto/August/Aug", 9: "septiembre/September/Sep", 10: "octubre/October/Oct",
    11: "noviembre/November/Nov", 12: "diciembre/December/Dec",
}


def interpret_ds(rows: list[list], anthropic_client, mes_numero: int | None = None) -> dict:
    filas = _enmascarar_montos(rows[:_MAX_FILAS_PROMPT])
    if mes_numero is not None:
        instruccion_mes = (
            f"El mes objetivo es el número {mes_numero} del año ({_MESES_NUMERO[mes_numero]}). "
            "Busca el bloque de 6 sub-columnas cuyo encabezado corresponda EXACTAMENTE a ese mes "
            "(en el idioma/formato que use el archivo) — ignora cualquier otro bloque, aunque tenga "
            "datos, incluyendo bloques de meses futuros vacíos o columnas de acumulado sin encabezado de mes."
        )
    else:
        instruccion_mes = "Identifica el bloque del mes más reciente presente en la hoja."
    prompt = (
        "Esta es una hoja de provisiones DS. Cada mes es un bloque de 6 sub-columnas "
        "(PROVISION/NUM.FACTURA/MONTO/Diferencia+/Diferencia-/Acumulados). Los montos se muestran "
        "como '#' — identifica la estructura por posición y encabezados, no por valores. "
        f"{instruccion_mes} Dentro de ese bloque, identifica la columna de PROVISION, la columna de "
        "código de proyecto, la columna CLIENTE, la columna NOMBRE (descripción del proyecto), la "
        "columna MONEDA (fuera del bloque mensual, es una columna general del proyecto — valores "
        "típicos MXN/USD), y en qué fila (índice) empiezan los datos de proyecto (después de "
        "encabezados). "
        "Responde solo JSON con las llaves: mes_columna, provision_columna, codigo_columna, "
        "cliente_columna, nombre_columna, moneda_columna, fila_inicio_datos. "
        f"{_INSTRUCCION_INDICE}\n\n"
        f"Filas: {filas}"
    )
    return _ask_claude_for_structure(anthropic_client, prompt)


def interpret_engineering(rows: list[list], anthropic_client, mes_numero: int | None = None) -> dict:
    filas = _enmascarar_montos(rows[:_MAX_FILAS_PROMPT])
    if mes_numero is not None:
        instruccion_mes = (
            f"El mes objetivo es el número {mes_numero} del año ({_MESES_NUMERO[mes_numero]}). "
            "Busca la columna cuyo encabezado corresponda EXACTAMENTE a ese mes (en inglés, "
            "abreviado o completo) — ignora cualquier otra columna, aunque tenga datos: no elijas un "
            "mes anterior ni uno posterior, ni una columna de total/acumulado sin encabezado de mes. "
            "Una fila individual puede tener '#'/None en esa columna sin que eso cambie cuál es la "
            "columna correcta — lo que define la columna es el encabezado, no cuántas filas tienen dato."
        )
    else:
        instruccion_mes = "Identifica la columna del mes más reciente presente en la hoja."
    prompt = (
        "Esta es una hoja de provisiones Engineering: una columna por mes en inglés, en orden "
        "cronológico de izquierda a derecha (Jan, Feb, Mar, Apr, May, ...), a veces hasta Diciembre "
        "aunque el año no haya terminado (meses futuros vacíos). Los montos se muestran como '#' — "
        f"identifica la estructura por posición y encabezados, no por valores. {instruccion_mes} "
        "Identifica también la columna de código de proyecto (formato código-cliente), la columna "
        "con el nombre/descripción del proyecto (texto libre, distinto del código), y en qué fila "
        "(índice) empiezan los datos de proyecto. "
        "Responde solo JSON con las llaves: mes_columna, codigo_columna, nombre_columna, fila_inicio_datos. "
        f"{_INSTRUCCION_INDICE}\n\n"
        f"Filas: {filas}"
    )
    return _ask_claude_for_structure(anthropic_client, prompt)


def interpret_consulting(rows: list[list], anthropic_client) -> dict:
    filas = _enmascarar_montos(rows[:_MAX_FILAS_PROMPT])
    prompt = (
        "Esta es la hoja Overview Consulting. Cada proyecto ocupa un bloque de varias filas; "
        "solo la primera fila del bloque tiene STATUS/PROJECT. El monto de provisión del proyecto "
        "es el valor de la columna llamada 'TOTAL' que está INMEDIATAMENTE A LA IZQUIERDA de la "
        "columna de MONEDA (encabezado '$'), tomado de la PRIMERA fila del bloque (la que tiene el "
        "STATUS). Ojo: puede haber otras columnas parecidas ('TOTAL EXP', 'Total' con minúscula) "
        "antes — la correcta es la 'TOTAL' pegada a la columna de moneda '$'. El código de proyecto "
        "viene en una celda multilínea (código\\ncliente\\ndescripción). Identifica las columnas de "
        "STATUS, PROJECT, la columna TOTAL (monto de provisión), y la columna de MONEDA del proyecto "
        "('$', valores tipo USD/MXN en la primera fila del bloque). "
        "Responde solo JSON con las llaves: status_columna, project_columna, "
        "total_columna, moneda_columna. "
        f"{_INSTRUCCION_INDICE}\n\n"
        f"Filas: {filas}"
    )
    return _ask_claude_for_structure(anthropic_client, prompt)


def interpret_notas_ds(notas, anthropic_client, anio_contexto: int):
    if not notas:
        return []
    prompt = (
        "Cada objeto tiene un 'codigo' de proyecto y una 'nota' de captura manual que indica a qué "
        "mes(es) de provisión corresponde una factura. La nota trae abreviaturas inconsistentes "
        "(ej. 'ENE26', 'feb26', 'DIC25', 'ago') y a veces montos o texto libre que debes ignorar. "
        "Para cada objeto devuelve el código y la lista de meses cubiertos, cada mes como cadena "
        "corta tipo 'ENE26' (mes de 3 letras + año de 2 dígitos si la nota lo indica). Si la nota no "
        "indica ningún mes claro, devuelve lista vacía para ese código. Responde ÚNICAMENTE un JSON "
        "array de objetos {codigo, meses}, sin explicación.\n\n"
        f"Notas: {notas}"
    )
    message = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        timeout=_TIMEOUT_SEGUNDOS,
        messages=[{"role": "user", "content": prompt}],
    )
    texto = message.content[0].text.strip()
    inicio, fin = texto.find("["), texto.rfind("]")
    datos = json.loads(texto[inicio:fin + 1]) if inicio != -1 else []
    pares = []
    for obj in datos:
        for mes_txt in obj.get("meses", []):
            normalizado = normalizar_periodo(mes_txt, anio_contexto=anio_contexto)
            if normalizado is not None:
                pares.append((obj["codigo"], normalizado[0], normalizado[1]))
    return pares


def interpret_facturacion(rows: list[list], anthropic_client) -> dict:
    filas = _enmascarar_montos(rows[:_MAX_FILAS_PROMPT])
    prompt = (
        "Esta es la hoja Detalle de Facturación. El código de proyecto viene con guión "
        "(código-cliente-descripción). Identifica la columna de proyecto, la columna de estado "
        "de la factura, la columna 'Periodo' — el mes de provisión que la factura cubre (es una "
        "fecha; NO la columna 'Fecha de factura' del timbrado) — y la columna 'Tipo de cambio' de "
        "la factura (valor 1 cuando es MXN, o el tipo de cambio numérico si es otra moneda). "
        "Responde solo JSON con las llaves: "
        "proyecto_columna, estado_columna, periodo_columna, tc_columna. "
        f"{_INSTRUCCION_INDICE}\n\n"
        f"Filas: {filas}"
    )
    return _ask_claude_for_structure(anthropic_client, prompt)
