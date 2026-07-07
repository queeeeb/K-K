def extraer_codigo(texto: str, formato: str) -> str:
    if formato == "limpio":
        return texto.strip()
    if formato == "guion":
        return texto.split("-")[0].strip()
    if formato == "multilinea":
        return texto.split("\n")[0].strip()
    raise ValueError(f"Formato de código desconocido: {formato}")


def cruzar_cierres(
    pares_facturacion: list[tuple[str, int, str]],
    pares_notas_ds: list[tuple[str, int, str]],
) -> tuple[list[dict], list[str]]:
    set_fact = set(pares_facturacion)
    set_notas = set(pares_notas_ds)
    cierres, alertas = [], []
    for par in sorted(set_fact | set_notas):
        codigo, anio, mes = par
        en_fact, en_notas = par in set_fact, par in set_notas
        if en_fact and en_notas:
            origen = "ambas"
        elif en_fact:
            origen = "facturacion"
            alertas.append(f"Cierre de {codigo} ({mes} {anio}) detectado solo en Facturación.")
        else:
            origen = "notas_ds"
            alertas.append(f"Cierre de {codigo} ({mes} {anio}) detectado solo en Notas DS.")
        cierres.append({"codigo": codigo, "anio": anio, "mes": mes, "origen": origen})
    return cierres, alertas


def reconciliar(
    provisiones_mes_anterior: list[dict],
    facturas_mes: list[dict],
    provisiones_actuales: list[dict],
    alertas: list[str] | None = None,
    codigos_conocidos: set[str] | None = None,
) -> dict:
    facturados = {
        extraer_codigo(f["proyecto"], formato="guion")
        for f in facturas_mes
        if f["estado"] in ("Sin pagar", "Pagado")
    }

    alertas = list(alertas or [])
    actuales_por_codigo = {
        extraer_codigo(p["proyecto"], formato="limpio"): p for p in provisiones_actuales
    }

    canceladas = []
    activas = []
    for provision in provisiones_mes_anterior:
        codigo = extraer_codigo(provision["proyecto"], formato="limpio")
        if codigo in facturados:
            canceladas.append(provision)
            continue

        actual = actuales_por_codigo.pop(codigo, None)
        if actual is not None:
            activas.append({
                **provision,
                "monto_mxn": actual["monto_mxn"],
                "monto_mxn_anterior": provision["monto_mxn"],
                "moneda": actual.get("moneda", provision.get("moneda", "MXN")),
                "monto_original": actual.get("monto_original", actual["monto_mxn"]),
                "tc": actual.get("tc", 1),
            })
        else:
            activas.append({**provision, "monto_mxn_anterior": provision["monto_mxn"]})
            alertas.append(
                f"Proyecto {codigo} no se encontró en ninguna fuente este mes ni fue facturado — "
                "se mantiene el monto anterior."
            )

    codigos_conocidos = codigos_conocidos or set()
    nuevas = [
        {**p, "codigo_nuevo": p["proyecto"] not in codigos_conocidos}
        for p in actuales_por_codigo.values()
    ]

    return {
        "canceladas": canceladas,
        "activas": activas,
        "nuevas": nuevas,
        "alertas": alertas,
    }


def actualizar_nombres_nuevas(plan: dict, nombres: dict[str, str]) -> dict:
    for p in plan["resumen"]["nuevas"]:
        if p["proyecto"] in nombres:
            p["cliente"] = nombres[p["proyecto"]]
            p["codigo_nuevo"] = False

    for fila in plan["detalle"]["filas"]:
        proyecto = fila[7]
        if proyecto in nombres:
            fila[5] = nombres[proyecto]

    return plan
