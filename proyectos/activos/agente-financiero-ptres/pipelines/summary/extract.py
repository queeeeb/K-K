def leer_provisiones_mes_anterior(wb, hoja: str) -> list[dict]:
    sheet = wb[hoja]
    provisiones = []
    for row in range(13, sheet.max_row + 1):
        cierre = sheet.cell(row=row, column=2).value
        if cierre is None or cierre.strip() != "Provision":
            continue
        provisiones.append({
            "proyecto": sheet.cell(row=row, column=8).value,
            "monto_mxn": sheet.cell(row=row, column=12).value,
            "cc": sheet.cell(row=row, column=5).value,
            "cliente": sheet.cell(row=row, column=6).value,
            "nombre_proyecto": sheet.cell(row=row, column=7).value or "",
            "moneda": sheet.cell(row=row, column=9).value or "MXN",
            "monto_original": sheet.cell(row=row, column=10).value,
            "tc": sheet.cell(row=row, column=11).value or 1,
            "anio": sheet.cell(row=row, column=3).value,
            "periodo": sheet.cell(row=row, column=4).value,
        })
    return provisiones


def leer_tipos_cambio(wb, hoja: str) -> dict:
    sheet = wb[hoja]
    tipos = {}
    for row in range(6, 9):
        moneda = sheet.cell(row=row, column=2).value
        if moneda:
            tipos[moneda.strip().upper()] = sheet.cell(row=row, column=3).value
    return tipos
