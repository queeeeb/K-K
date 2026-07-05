def extraer_codigo(texto: str, formato: str) -> str:
    if formato == "limpio":
        return texto.strip()
    if formato == "guion":
        return texto.split("-")[0].strip()
    if formato == "multilinea":
        return texto.split("\n")[0].strip()
    raise ValueError(f"Formato de código desconocido: {formato}")


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
