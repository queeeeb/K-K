import re


_SEGMENTOS_VALIDOS = {2000, 3000, 7000}
_STATUS_CONSULTING_ACTIVOS = {"PROVISION", "FACTURADO"}


def _cc_desde_codigo(codigo: str) -> int | None:
    match = re.search(r"gmx(\d+)\.", codigo)
    if not match:
        return None
    cc = int(match.group(1))
    return cc if cc in _SEGMENTOS_VALIDOS else None


def extraer_ds(rows: list[list], estructura: dict) -> list[dict]:
    codigo_col = estructura["codigo_columna"]
    provision_col = estructura["provision_columna"]
    resultado = []
    for i in range(estructura["fila_inicio_datos"], len(rows)):
        codigo = rows[i][codigo_col]
        if not isinstance(codigo, str) or not codigo.strip():
            continue
        resultado.append({
            "proyecto": codigo,
            "monto_mxn": rows[i][provision_col],
            "cc": _cc_desde_codigo(codigo),
            "cliente": "",
        })
    return resultado


def extraer_engineering(rows: list[list], estructura: dict) -> list[dict]:
    codigo_col = estructura["codigo_columna"]
    mes_col = estructura["mes_columna"]
    resultado = []
    for i in range(estructura["fila_inicio_datos"], len(rows)):
        crudo = rows[i][codigo_col]
        if not isinstance(crudo, str) or not crudo.strip():
            continue
        proyecto, _, cliente = crudo.partition("-")
        resultado.append({
            "proyecto": proyecto.strip(),
            "monto_mxn": rows[i][mes_col],
            "cc": _cc_desde_codigo(proyecto.strip()),
            "cliente": cliente.strip(),
        })
    return resultado


def extraer_consulting(rows: list[list], estructura: dict) -> list[dict]:
    status_col = estructura["status_columna"]
    project_col = estructura["project_columna"]
    trigger_col = estructura["trigger_columna"]
    monto_col = estructura["monto_columna"]

    resultado = []
    bloque = None
    for row in rows[1:]:
        status = row[status_col]
        if status:
            if bloque is not None:
                resultado.append(bloque)
            if status.strip() in _STATUS_CONSULTING_ACTIVOS:
                lineas = row[project_col].split("\n")
                bloque = {
                    "proyecto": lineas[0].strip(),
                    "cliente": lineas[1].strip() if len(lineas) > 1 else "",
                    "monto_mxn": 0,
                    "cc": _cc_desde_codigo(lineas[0].strip()),
                }
            else:
                bloque = None
        if bloque is not None:
            trigger = row[trigger_col]
            if isinstance(trigger, str) and trigger.strip() == "Total honorarios":
                monto = row[monto_col]
                if monto:
                    bloque["monto_mxn"] += monto
    if bloque is not None:
        resultado.append(bloque)
    return resultado


def extraer_facturacion(rows: list[list], estructura: dict) -> list[dict]:
    proyecto_col = estructura["proyecto_columna"]
    estado_col = estructura["estado_columna"]
    return [
        {"proyecto": row[proyecto_col], "estado": row[estado_col]}
        for row in rows[1:]
        if row[proyecto_col]
    ]
