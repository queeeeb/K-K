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
    provisiones_nuevas: list[dict],
    alertas: list[str] | None = None,
) -> dict:
    facturados = {
        extraer_codigo(f["proyecto"], formato="guion")
        for f in facturas_mes
        if f["estado"] in ("Sin pagar", "Pagado")
    }

    canceladas = []
    activas = []
    for provision in provisiones_mes_anterior:
        codigo = extraer_codigo(provision["proyecto"], formato="limpio")
        if codigo in facturados:
            canceladas.append(provision)
        else:
            activas.append({**provision, "monto_mxn_anterior": provision["monto_mxn"]})

    return {
        "canceladas": canceladas,
        "activas": activas,
        "nuevas": list(provisiones_nuevas),
        "alertas": alertas or [],
    }
