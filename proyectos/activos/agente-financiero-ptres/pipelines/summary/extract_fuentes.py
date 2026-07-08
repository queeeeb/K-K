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
    total_col = estructura["total_columna"]
    moneda_col = estructura.get("moneda_columna")

    resultado = []
    for row in rows[1:]:
        status = row[status_col]
        if not isinstance(status, str) or status.strip() not in _STATUS_CONSULTING_ACTIVOS:
            continue
        monto = row[total_col]
        if not monto or abs(monto) < _PROVISION_MINIMA:
            continue
        lineas = row[project_col].split("\n")
        codigo = lineas[0].strip().rstrip("-. ").strip()
        moneda = _texto(row[moneda_col]).upper() if moneda_col is not None else ""
        resultado.append({
            "proyecto": codigo,
            "cliente": lineas[1].strip() if len(lineas) > 1 else "",
            "nombre_proyecto": "\n".join(l.strip() for l in lineas[2:]) if len(lineas) > 2 else "",
            "monto_mxn": monto,
            "cc": _cc_desde_codigo(codigo),
            "moneda": moneda or "MXN",
        })
    return resultado


def _moneda_por_tc(tc, tipos_cambio: dict, tolerancia: float = 0.05) -> str | None:
    if not isinstance(tc, (int, float)):
        return None
    if abs(tc - 1) < 1e-6:
        return "MXN"
    mejor, mejor_dif = None, None
    for moneda, ref in tipos_cambio.items():
        if not ref or ref <= 1:
            continue
        dif = abs(tc - ref) / ref
        if mejor_dif is None or dif < mejor_dif:
            mejor, mejor_dif = moneda, dif
    return mejor if mejor_dif is not None and mejor_dif <= tolerancia else None


def monedas_engineering_facturacion(rows: list[list], estructura: dict, tipos_cambio: dict) -> dict:
    proyecto_col = estructura["proyecto_columna"]
    tc_col = estructura["tc_columna"]
    monedas = {}
    for row in rows[1:]:
        proyecto = row[proyecto_col]
        if not isinstance(proyecto, str) or "gmx2000" not in proyecto:
            continue
        codigo = extraer_codigo(proyecto, formato="guion")
        moneda = _moneda_por_tc(row[tc_col], tipos_cambio)
        if moneda is not None:
            monedas[codigo] = moneda
    return monedas


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
