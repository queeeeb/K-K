from openpyxl import load_workbook


def _duplicate_sheet(wb, origen_titulo: str, nuevo_titulo: str):
    origen = wb[origen_titulo]
    nueva = wb.copy_worksheet(origen)
    nueva.title = nuevo_titulo
    return nueva


def _limpiar_seccion_b(sheet) -> None:
    for row in sheet.iter_rows(min_row=12, max_row=sheet.max_row):
        for cell in row:
            cell.value = None


def escribir_hoja_mes(
    ruta_origen: str,
    ruta_destino: str,
    hoja_mes_anterior: str,
    hoja_mes_nuevo: str,
    filas: list[list],
) -> None:
    wb = load_workbook(ruta_origen, keep_vba=ruta_origen.endswith(".xlsm"))
    nueva = _duplicate_sheet(wb, hoja_mes_anterior, hoja_mes_nuevo)
    _limpiar_seccion_b(nueva)

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

    wb.save(ruta_destino)
