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
        })
    return provisiones
