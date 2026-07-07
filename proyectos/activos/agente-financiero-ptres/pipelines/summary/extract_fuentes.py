import re

from pipelines.summary.calculate import extraer_codigo
from pipelines.summary.periodos import normalizar_periodo


_SEGMENTOS_VALIDOS = {2000, 3000, 7000}
_ESTADOS_FACTURADO = {"Sin pagar", "Pagado"}
_STATUS_CONSULTING_ACTIVOS = {"PROVISION", "FACTURADO"}


def _cc_desde_codigo(codigo: str) -> int | None:
    match = re.search(r"gmx(\d+)\.", codigo)
    if not match:
        return None
    cc = int(match.group(1))
    return cc if cc in _SEGMENTOS_VALIDOS else None


def _texto(valor) -> str:
    return valor.strip() if isinstance(valor, str) else ""


_PROVISION_MINIMA = 0.01


def extraer_ds(rows: list[list], estructura: dict) -> list[dict]:
    codigo_col = estructura["codigo_columna"]
    provision_col = estructura["provision_columna"]
    cliente_col = estructura["cliente_columna"]
    nombre_col = estructura["nombre_columna"]
    moneda_col = estructura.get("moneda_columna")
    resultado = []
    for i in range(estructura["fila_inicio_datos"], len(rows)):
        codigo = rows[i][codigo_col]
        if not isinstance(codigo, str) or not codigo.strip():
            continue
        monto = rows[i][provision_col]
        if not monto or abs(monto) < _PROVISION_MINIMA:
            continue
        codigo_limpio = codigo.strip().rstrip("-. ").strip()
        moneda = _texto(rows[i][moneda_col]).upper() if moneda_col is not None else ""
        resultado.append({
            "proyecto": codigo_limpio,
            "monto_mxn": monto,
            "cc": _cc_desde_codigo(codigo_limpio),
            "cliente": _texto(rows[i][cliente_col]),
            "nombre_proyecto": _texto(rows[i][nombre_col]),
            "moneda": moneda or "MXN",
        })
    return resultado


def extraer_engineering(rows: list[list], estructura: dict) -> list[dict]:
    codigo_col = estructura["codigo_columna"]
    mes_col = estructura["mes_columna"]
    nombre_col = estructura["nombre_columna"]
    resultado = []
    for i in range(estructura["fila_inicio_datos"], len(rows)):
        crudo = rows[i][codigo_col]
        if not isinstance(crudo, str) or not crudo.strip():
            continue
        monto = rows[i][mes_col]
        if not monto or abs(monto) < _PROVISION_MINIMA:
            continue
        proyecto, _, cliente = crudo.partition("-")
        resultado.append({
            "proyecto": proyecto.strip(),
            "monto_mxn": monto,
            "cc": _cc_desde_codigo(proyecto.strip()),
            "cliente": cliente.strip(),
            "nombre_proyecto": _texto(rows[i][nombre_col]),
            "moneda": "MXN",
        })
    return resultado


def extraer_consulting(rows: list[list], estructura: dict) -> list[dict]:
    status_col = estructura["status_columna"]
    project_col = estructura["project_columna"]
    trigger_col = estructura["trigger_columna"]
    monto_col = estructura["monto_columna"]
    moneda_col = estructura.get("moneda_columna")

    resultado = []
    bloque = None
    for row in rows[1:]:
        status = row[status_col]
        if status:
            if bloque is not None:
                resultado.append(bloque)
            if status.strip() in _STATUS_CONSULTING_ACTIVOS:
                lineas = row[project_col].split("\n")
                codigo = lineas[0].strip().rstrip("-. ").strip()
                moneda = _texto(row[moneda_col]).upper() if moneda_col is not None else ""
                bloque = {
                    "proyecto": codigo,
                    "cliente": lineas[1].strip() if len(lineas) > 1 else "",
                    "nombre_proyecto": "\n".join(l.strip() for l in lineas[2:]) if len(lineas) > 2 else "",
                    "monto_mxn": 0,
                    "cc": _cc_desde_codigo(codigo),
                    "moneda": moneda or "MXN",
                }
            else:
                bloque = None
        if bloque is not None:
            trigger = row[trigger_col]
            if isinstance(trigger, str) and trigger.strip().startswith("Total honorarios"):
                monto = row[monto_col]
                if monto:
                    bloque["monto_mxn"] += monto
    if bloque is not None:
        resultado.append(bloque)
    return resultado


def pares_cierre_facturacion(rows: list[list], estructura: dict) -> list[tuple[str, int, str]]:
    proyecto_col = estructura["proyecto_columna"]
    estado_col = estructura["estado_columna"]
    periodo_col = estructura["periodo_columna"]
    pares = []
    for row in rows[1:]:
        if not row[proyecto_col] or _texto(row[estado_col]) not in _ESTADOS_FACTURADO:
            continue
        periodo = normalizar_periodo(row[periodo_col])
        if periodo is None:
            continue
        codigo = extraer_codigo(row[proyecto_col], formato="guion")
        pares.append((codigo, periodo[0], periodo[1]))
    return pares
