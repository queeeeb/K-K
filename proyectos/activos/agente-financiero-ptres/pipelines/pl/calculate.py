"""Núcleo determinista del P&L: reglas de signo, acumulación por cuenta×segmento,
subtotales y porcentajes. La IA nunca pasa por aquí — solo valores ya extraídos.
Ver pipelines/pl/ESPECIFICACION.md §3.3 y §3.6.
"""

SEGMENTOS = ["BO", "CONS OPS", "ING", "DIGITAL SOLUTIONS"]
COLUMNAS_SALIDA = SEGMENTOS + ["TOTAL"]
RUBROS = ["INCOMES", "EXPENSES", "OTHER_INCOMES", "OTHER_EXPENSES", "ACCRUED_TAXES"]

# Cuenta lump-sum de ventas nacionales: se excluye de la base de % porque se
# reemplaza por su desglose por cliente (ver §3.6).
CUENTA_VENTAS_NACIONALES = "4110-001-001-000"


def es_ingreso(numero_cuenta: str) -> bool:
    """Regla de signo: las cuentas de ingreso empiezan en 4."""
    return numero_cuenta.strip().startswith("4")


def monto_neto(cargos: float, abonos: float, ingreso: bool) -> float:
    """Ingreso = abonos - cargos. Gasto = cargos - abonos. (§3.3, invariante)."""
    return (abonos - cargos) if ingreso else (cargos - abonos)


def safe_pct(monto: float, base: float) -> float:
    return 0.0 if base == 0 else monto / base


def _netos_de_cuenta(cuenta: dict) -> dict:
    ingreso = es_ingreso(cuenta["numero"])
    netos: dict = {}
    total = 0.0
    for seg in SEGMENTOS:
        mov = cuenta.get("segmentos", {}).get(seg, {})
        valor = monto_neto(mov.get("cargos", 0) or 0, mov.get("abonos", 0) or 0, ingreso)
        netos[seg] = valor
        total += valor
    netos["TOTAL"] = total
    return netos


def calcular_pl(cuentas: list[dict]) -> dict:
    """Recibe cuentas ya clasificadas (numero, label, rubro, segmentos:{seg:{cargos,abonos}})
    y devuelve el plan: filas por rubro, totales/subtotales derivados y base de %.
    """
    netos_por_cuenta = [(c, _netos_de_cuenta(c)) for c in cuentas]

    totales = {r: {col: 0.0 for col in COLUMNAS_SALIDA} for r in RUBROS}
    base = {col: 0.0 for col in COLUMNAS_SALIDA}

    for cuenta, netos in netos_por_cuenta:
        rubro = cuenta["rubro"]
        if rubro not in totales:
            continue  # cuenta no clasificada a un rubro del P&L: se ignora
        for col in COLUMNAS_SALIDA:
            totales[rubro][col] += netos[col]
        if rubro == "INCOMES" and cuenta["numero"].strip() != CUENTA_VENTAS_NACIONALES:
            for col in COLUMNAS_SALIDA:
                base[col] += netos[col]

    operating = {
        col: totales["INCOMES"][col] - totales["EXPENSES"][col] for col in COLUMNAS_SALIDA
    }
    net = {
        col: operating[col]
        + totales["OTHER_INCOMES"][col]
        - totales["OTHER_EXPENSES"][col]
        - totales["ACCRUED_TAXES"][col]
        for col in COLUMNAS_SALIDA
    }

    rubros_filas: dict = {r: [] for r in RUBROS}
    for cuenta, netos in netos_por_cuenta:
        rubro = cuenta["rubro"]
        if rubro not in rubros_filas:
            continue
        rubros_filas[rubro].append(
            {
                "numero": cuenta["numero"],
                "label": cuenta.get("label", cuenta["numero"]),
                "montos": netos,
                "pct": {col: safe_pct(netos[col], base[col]) for col in COLUMNAS_SALIDA},
            }
        )

    totales_salida = dict(totales)
    totales_salida["OPERATING_PROFIT"] = operating
    totales_salida["NET_PROFIT"] = net

    return {"rubros": rubros_filas, "totales": totales_salida, "base_ingresos": base}
