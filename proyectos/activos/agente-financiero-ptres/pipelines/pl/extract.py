import re

SEGMENTOS_CANONICOS = {"BO", "ING", "CONS OPS", "DIGITAL SOLUTIONS"}
_CUENTA_RE = re.compile(r"^\d{4}-")


def _normalizar_segmento(texto: str) -> str | None:
    m = re.match(r"Segmento:\s*\d+\s+(.+)", texto.strip())
    if not m:
        return None
    nombre = m.group(1).strip()
    return nombre if nombre in SEGMENTOS_CANONICOS else None


def _es_cuenta(valor) -> bool:
    return isinstance(valor, str) and bool(_CUENTA_RE.match(valor.strip()))


def extraer_cuentas(ws) -> list[dict]:
    cuentas = []
    cuenta_actual = None
    seg_actual = None

    for i in range(1, ws.max_row + 1):
        a = ws.cell(row=i, column=1).value
        b = ws.cell(row=i, column=2).value
        e = ws.cell(row=i, column=5).value
        try:
            f_val = float(ws.cell(row=i, column=6).value or 0)
            g_val = float(ws.cell(row=i, column=7).value or 0)
        except (TypeError, ValueError):
            f_val, g_val = 0.0, 0.0

        a_str = str(a).strip() if a is not None else ""
        e_str = str(e).strip() if e is not None else ""

        if _es_cuenta(a_str):
            nombre = str(b).strip() if b is not None else ""
            cuenta_actual = {"numero": a_str, "nombre": nombre, "segmentos": {}}
            cuentas.append(cuenta_actual)
            seg_actual = None

        elif a_str.startswith("Segmento:"):
            seg_actual = _normalizar_segmento(a_str)
            if seg_actual and cuenta_actual is not None:
                # Captura inmediata como fallback para cuentas sin Total Seg. explícito
                cuenta_actual["segmentos"][seg_actual] = {"cargos": f_val, "abonos": g_val}

        elif e_str.startswith("Total Seg.") and cuenta_actual is not None and seg_actual is not None:
            # Sobreescribe con el valor confirmado del Total Seg.
            cuenta_actual["segmentos"][seg_actual] = {"cargos": f_val, "abonos": g_val}
            seg_actual = None

    return cuentas
