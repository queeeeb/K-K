from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill


def _duplicate_sheet(wb, origen_titulo: str, nuevo_titulo: str):
    origen = wb[origen_titulo]
    nueva = wb.copy_worksheet(origen)
    nueva.title = nuevo_titulo
    return nueva


_SIN_RELLENO = PatternFill(fill_type=None)


def _limpiar_formato(sheet) -> None:
    for row in sheet.iter_rows():
        for cell in row:
            cell.fill = _SIN_RELLENO
            cell.font = Font(name=cell.font.name, size=cell.font.size)
            if cell.comment is not None:
                cell.comment = None


def _limpiar_seccion_b(sheet) -> None:
    for row in sheet.iter_rows(min_row=12, max_row=sheet.max_row):
        for cell in row:
            cell.value = None


_COL_KPI_POR_UNIDAD = {3000: 9, 2000: 10, 7000: 11}


def _actualizar_formulas_kpi(sheet, ultima_fila: int) -> None:
    for col, cc in ((9, 3000), (10, 2000), (11, 7000)):
        sheet.cell(row=2, column=col, value=(
            f'=SUMIFS(L13:L{ultima_fila},E13:E{ultima_fila},{cc},B13:B{ultima_fila},"Provision")'
        ))
        sheet.cell(row=4, column=col, value=(
            f'=SUMIF(E13:Q{ultima_fila},{cc},Q13:Q{ultima_fila})'
        ))


def _poblar_facturacion_kpi(sheet, concentrado: dict) -> list[str]:
    if not concentrado:
        for col in _COL_KPI_POR_UNIDAD.values():
            sheet.cell(row=3, column=col, value=None)
            sheet.cell(row=5, column=col, value=None)
        return ["Hoja Concentrado ausente en Facturación — filas 3 y 5 del KPI quedaron en blanco."]
    for unidad, col in _COL_KPI_POR_UNIDAD.items():
        datos = concentrado.get(unidad, {})
        sheet.cell(row=3, column=col, value=datos.get("facturado"))
        sheet.cell(row=5, column=col, value=datos.get("canceladas"))
    return []


def _poblar_antiguas_por_facturar(sheet, filas: list[list], mes_actual: str) -> None:
    suma = {3000: 0.0, 2000: 0.0, 7000: 0.0}
    for fila in filas:
        cierre = fila[1].strip() if isinstance(fila[1], str) else ""
        periodo = fila[3].strip() if isinstance(fila[3], str) else ""
        unidad, monto = fila[4], fila[11]
        if cierre.startswith("Provision") and periodo != mes_actual and unidad in suma:
            if isinstance(monto, (int, float)):
                suma[unidad] += monto
    for unidad, col in _COL_KPI_POR_UNIDAD.items():
        sheet.cell(row=11, column=col, value=suma[unidad] or 0)


_FILA_TC = {"USD": 6, "EUR": 7, "CAD": 8}


def _escribir_tipos_cambio(sheet, tipos_cambio: dict) -> None:
    for moneda, fila in _FILA_TC.items():
        valor = tipos_cambio.get(moneda)
        if valor is not None:
            sheet.cell(row=fila, column=3, value=valor)


def escribir_hoja_mes(
    ruta_origen: str,
    ruta_destino: str,
    hoja_mes_anterior: str,
    hoja_mes_nuevo: str,
    filas: list[list],
    concentrado: dict,
    mes_actual: str,
    tipos_cambio: dict | None = None,
) -> list[str]:
    wb = load_workbook(ruta_origen, keep_vba=ruta_origen.endswith(".xlsm"))
    nueva = _duplicate_sheet(wb, hoja_mes_anterior, hoja_mes_nuevo)
    _limpiar_seccion_b(nueva)
    if tipos_cambio:
        _escribir_tipos_cambio(nueva, tipos_cambio)

    encabezados = [
        "Cotizacion", "Cierre", "Año", "Periodo", "CC", "Cliente", "Nombre Proyecto",
        "Proyecto", "Moneda", "Provision", "T/C Provision", "PROVISION MXN", "usd",
        "MXN", "EUR", "CAD", "TOTAL MXN", "Referencia", "Comentarios",
    ]
    for col, header in enumerate(encabezados, start=1):
        nueva.cell(row=12, column=col, value=header)

    for offset, fila in enumerate(filas, start=13):
        for col, valor in enumerate(fila, start=1):
            nueva.cell(row=offset, column=col, value=valor)

    ultima_fila = 12 + len(filas) if filas else 13
    _actualizar_formulas_kpi(nueva, ultima_fila)
    alertas = _poblar_facturacion_kpi(nueva, concentrado)
    _poblar_antiguas_por_facturar(nueva, filas, mes_actual)
    _limpiar_formato(nueva)

    wb.save(ruta_destino)
    return alertas
