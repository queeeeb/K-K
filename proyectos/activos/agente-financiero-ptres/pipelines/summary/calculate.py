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
    ledger_vivo: list[dict],
    cierres: list[dict],
    provisiones_actuales: list[dict],
    alertas: list[str] | None = None,
    codigos_conocidos: set[str] | None = None,
) -> dict:
    alertas = list(alertas or [])
    codigos_conocidos = codigos_conocidos or set()

    cierres_por_clave = {(c["codigo"], c["anio"], c["mes"]): c for c in cierres}
    claves_aplicadas = set()

    mantenidas, cerradas = [], []
    for fila in ledger_vivo:
        clave = (fila["proyecto"], fila.get("anio"), fila.get("periodo"))
        if clave in cierres_por_clave:
            cerradas.append(fila)
            claves_aplicadas.add(clave)
        else:
            mantenidas.append(fila)

    for clave, cierre in cierres_por_clave.items():
        if clave not in claves_aplicadas:
            codigo, anio, mes = clave
            alertas.append(
                f"Cierre de {codigo} ({mes} {anio}, origen {cierre['origen']}) no encontró "
                "fila abierta en el ledger — no se aplicó, requiere revisión manual."
            )

    nuevas = [
        {**p, "codigo_nuevo": p["proyecto"] not in codigos_conocidos}
        for p in provisiones_actuales
    ]

    return {
        "mantenidas": mantenidas,
        "cerradas": cerradas,
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
