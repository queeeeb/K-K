import re

SEGMENTOS_CANONICOS = {"BO", "ING", "CONS OPS", "DIGITAL SOLUTIONS"}
CUENTA_VENTAS_NACIONALES = "4110-001-001-000"
_CUENTA_RE = re.compile(r"^\d{4}-")


def _normalizar_segmento(texto: str) -> str | None:
    m = re.match(r"Segmento:\s*\d+\s+(.+)", texto.strip())
    if not m:
        return None
    nombre = m.group(1).strip()
    return nombre if nombre in SEGMENTOS_CANONICOS else None


def _es_cuenta(valor) -> bool:
    return isinstance(valor, str) and bool(_CUENTA_RE.match(valor.strip()))


def _num(valor) -> float:
    try:
        return float(valor or 0)
    except (TypeError, ValueError):
        return 0.0


def extraer(ws) -> dict:
    """Recorre el reporte jerárquico de Contpaqi en una sola pasada y devuelve:
    - `cuentas`: cuentas con sus montos por segmento (Total Seg.).
    - `ventas_nacionales`: desglose de la cuenta lump-sum de ventas nacionales por
      cliente (col D) y segmento, a partir de las filas `Diario` (§3.4).
    """
    cuentas = []
    cuenta_actual = None
    seg_actual = None
    en_ventas_nacionales = False
    ns_acumulado: dict[tuple[str, str], float] = {}

    for i in range(1, ws.max_row + 1):
        a = ws.cell(row=i, column=1).value
        b = ws.cell(row=i, column=2).value
        d = ws.cell(row=i, column=4).value
        e = ws.cell(row=i, column=5).value
        f_val = _num(ws.cell(row=i, column=6).value)
        g_val = _num(ws.cell(row=i, column=7).value)

        a_str = str(a).strip() if a is not None else ""
        b_str = str(b).strip() if b is not None else ""
        e_str = str(e).strip() if e is not None else ""

        if _es_cuenta(a_str):
            nombre = str(b).strip() if b is not None else ""
            cuenta_actual = {"numero": a_str, "nombre": nombre, "segmentos": {}}
            cuentas.append(cuenta_actual)
            seg_actual = None
            en_ventas_nacionales = a_str == CUENTA_VENTAS_NACIONALES

        elif a_str.startswith("Segmento:"):
            seg_actual = _normalizar_segmento(a_str)
            if seg_actual and cuenta_actual is not None:
                cuenta_actual["segmentos"][seg_actual] = {"cargos": f_val, "abonos": g_val}

        elif en_ventas_nacionales and seg_actual is not None and b_str == "Diario":
            cliente = str(d).strip() if d is not None else ""
            if cliente:
                clave = (cliente, seg_actual)
                ns_acumulado[clave] = ns_acumulado.get(clave, 0.0) + g_val

        elif e_str.startswith("Total Seg.") and cuenta_actual is not None and seg_actual is not None:
            cuenta_actual["segmentos"][seg_actual] = {"cargos": f_val, "abonos": g_val}
            seg_actual = None

    ventas_nacionales = [
        {"cliente": cliente, "segmento": segmento, "monto": monto}
        for (cliente, segmento), monto in ns_acumulado.items()
    ]
    return {"cuentas": cuentas, "ventas_nacionales": ventas_nacionales}


def extraer_cuentas(ws) -> list[dict]:
    return extraer(ws)["cuentas"]
