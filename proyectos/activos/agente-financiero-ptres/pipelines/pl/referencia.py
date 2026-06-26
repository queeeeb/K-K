"""Catálogo de referencia/semilla portado del macro VBA (GenerarPL.bas).

NO es el mecanismo que decide la clasificación en producción: la IA (interpret.py)
clasifica y traduce dinámicamente. Esto es la semilla de validación / glosario para
mantener los mismos labels que la referencia del cliente y para tests deterministas.
Ver pipelines/pl/ESPECIFICACION.md §3.2, §3.5 y §7.
"""

# Prefijo de cuenta -> grupo (espejo de GetGrp en el macro)
RUBRO_POR_GRUPO = {
    "4110": "INCOMES",
    "4210": "OTHER_INCOMES",
    "4310": "OTHER_INCOMES",
    "4510": "OTHER_INCOMES",
    "6001": "EXPENSES",
    "6002": "EXPENSES",
    "6004": "EXPENSES",
    "6005": "EXPENSES",
    "6006": "EXPENSES",
    "6007": "EXPENSES",
    "6008": "EXPENSES",
    "6009": "OTHER_EXPENSES",
    "8000": "ACCRUED_TAXES",
}

# Glosario ES -> EN (subconjunto representativo del diccionario `EN` del macro).
# Semilla para que la IA conserve labels idénticos a la referencia; no es exhaustivo.
GLOSARIO_ES_EN = {
    "VENTAS NACIONALES": "NATIONAL SALES",
    "SUELDOS Y SALARIOS": "  GENERAL DEP",
    "AGUINALDO": "  CHRISTMAS BONUS",
    "VACACIONES": "  VACATIONS",
    "PRIMA VACACIONAL": "  VACATIONS PREMIUM",
    "I.M.S.S.": "  SOCIAL SECURITY CONTRIBUTIONS",
    "IMPUESTOS SOBRE NOMINA": "  PAYROLL TAX",
    "TELEFONO": "  TELEPHONE",
    "ESTACIONAMIENTOS": "  PARKING",
    "UTILIDAD CAMBIARIA": "  E.R. FLUCTUATION PROFIT",
    "OTROS INGRESOS": "  OTHER INCOME",
    "INTERESES A FAVOR": "  INTEREST",
    "PRODUCTOS FINANCIEROS": "  FINANCIAL PRODUCTS",
    "PERDIDA CAMBIARIA": "  E.R. FLUCTUATION LOSS",
    "COMISIONES BANCARIAS": "  BANK COMMISIONS",
    "INTERESES A CARGO": "  INTEREST EXPENSE",
    "I.S.R. DEL EJERCICIO": "  INCOME TAX OF THE YEAR",
    "P.T.U.": "  PTU",
}


def grupo_por_numero(numero_cuenta: str) -> str:
    """Devuelve el grupo del macro a partir del número de cuenta, o '' si no aplica."""
    c = numero_cuenta.strip()
    if c[:4] == "4110":
        return "4110"
    if c[:4] == "4210":
        return "4210"
    if c[:4] == "4310":
        return "4310"
    if c[:4] == "4510":
        return "4510"
    for sufijo, grupo in (
        ("6100-001", "6001"),
        ("6100-002", "6002"),
        ("6100-004", "6004"),
        ("6100-005", "6005"),
        ("6100-006", "6006"),
        ("6100-007", "6007"),
        ("6100-008", "6008"),
        ("6100-009", "6009"),
    ):
        if c[:8] == sufijo:
            return grupo
    if c[:11] == "0000-000-80" or c[:4] == "8000":
        return "8000"
    return ""


def clasificar_por_numero(numero_cuenta: str) -> tuple[str, str]:
    """(grupo, rubro) deterministas de referencia. rubro == '' si la cuenta se ignora."""
    grupo = grupo_por_numero(numero_cuenta)
    return grupo, RUBRO_POR_GRUPO.get(grupo, "")


def traducir(nombre_es: str) -> str:
    """Traducción ES->EN de referencia; si no está en el glosario, deja el nombre indentado."""
    return GLOSARIO_ES_EN.get(nombre_es.strip().upper(), "  " + nombre_es.strip())
