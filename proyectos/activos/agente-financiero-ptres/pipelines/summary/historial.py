from pipelines.summary.calculate import normalizar_codigo


def buscar_codigo_en_historial(wb, hojas_ordenadas: list[str], codigo: str) -> str | None:
    for hoja in reversed(hojas_ordenadas):
        sheet = wb[hoja]
        for row in range(13, sheet.max_row + 1):
            if normalizar_codigo(sheet.cell(row=row, column=8).value) == codigo:
                return hoja
    return None


def todos_los_codigos_conocidos(wb, hojas_ordenadas: list[str]) -> set[str]:
    codigos = set()
    for hoja in hojas_ordenadas:
        sheet = wb[hoja]
        for row in range(13, sheet.max_row + 1):
            codigo = sheet.cell(row=row, column=8).value
            if codigo:
                codigos.add(normalizar_codigo(codigo))
    return codigos
