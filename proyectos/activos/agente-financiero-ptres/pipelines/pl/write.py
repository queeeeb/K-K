"""Escritura determinista del P&L con openpyxl: hojas CONSOLIDATED y BY SEGMENT,
en el orden de secciones de la referencia. No decide nada — solo vuelca el plan.
Ver pipelines/pl/ESPECIFICACION.md §2 y §5.
"""
from openpyxl import Workbook

from pipelines.pl.calculate import COLUMNAS_SALIDA, SEGMENTOS, safe_pct

ETIQUETAS_SEGMENTO = ["BACK OFFICE", "CONSUL OP", "ENGINEERING", "DIGITAL SOLUTIONS"]
FMT_MONTO = "#,##0.00"
FMT_PCT = "0.00%"


def _escribir_fila(sheet, r, label, montos, pct, consolidado):
    sheet.cell(row=r, column=1, value=label)
    if consolidado:
        c = sheet.cell(row=r, column=2, value=montos["TOTAL"])
        c.number_format = FMT_MONTO
        c = sheet.cell(row=r, column=3, value=pct["TOTAL"])
        c.number_format = FMT_PCT
    else:
        for i, seg in enumerate(SEGMENTOS):
            c = sheet.cell(row=r, column=2 + i * 2, value=montos[seg])
            c.number_format = FMT_MONTO
            c = sheet.cell(row=r, column=3 + i * 2, value=pct[seg])
            c.number_format = FMT_PCT
        c = sheet.cell(row=r, column=10, value=montos["TOTAL"])
        c.number_format = FMT_MONTO
        c = sheet.cell(row=r, column=11, value=pct["TOTAL"])
        c.number_format = FMT_PCT


def _escribir_hoja(sheet, plan, periodo, consolidado):
    base = plan["base_ingresos"]
    totales = plan["totales"]
    rubros = plan["rubros"]

    def pct_de(montos):
        return {col: safe_pct(montos[col], base[col]) for col in COLUMNAS_SALIDA}

    r = 1
    sheet.cell(row=r, column=1, value="P-TRES GROUP, S.A.P.I. DE C.V.")
    r += 1
    sufijo = " — " if consolidado else " by Segment — "
    sheet.cell(row=r, column=1, value="Profit and Loss Statement" + sufijo + str(periodo))
    r += 2

    sheet.cell(row=r, column=1, value="DESCRIPTION")
    if consolidado:
        sheet.cell(row=r, column=2, value="TOTAL")
        sheet.cell(row=r, column=3, value="%")
    else:
        for i, etq in enumerate(ETIQUETAS_SEGMENTO):
            sheet.cell(row=r, column=2 + i * 2, value=etq)
            sheet.cell(row=r, column=3 + i * 2, value="%")
        sheet.cell(row=r, column=10, value="TOTAL")
        sheet.cell(row=r, column=11, value="%")
    r += 1

    # Secciones con detalle + fila de total
    secciones = [
        ("Incomes", "INCOMES", "Incomes Total"),
        ("Expenses", "EXPENSES", "Expenses Total"),
    ]
    for titulo, rubro, total_label in secciones:
        sheet.cell(row=r, column=1, value=titulo)
        r += 1
        for fila in rubros[rubro]:
            _escribir_fila(sheet, r, fila["label"], fila["montos"], fila["pct"], consolidado)
            r += 1
        _escribir_fila(sheet, r, total_label, totales[rubro], pct_de(totales[rubro]), consolidado)
        r += 2

    # Operating profit (subtotal derivado)
    _escribir_fila(
        sheet, r, "OPERATING PROFIT (OR LOSS) BEFORE ALLOCATIONS",
        totales["OPERATING_PROFIT"], pct_de(totales["OPERATING_PROFIT"]), consolidado,
    )
    r += 2

    for titulo, rubro, total_label in [
        ("Other Incomes", "OTHER_INCOMES", "Other Incomes Total"),
        ("Other Expenses", "OTHER_EXPENSES", "Other Expenses Total"),
        ("Accrued Taxes", "ACCRUED_TAXES", "Accrued Taxes Total"),
    ]:
        sheet.cell(row=r, column=1, value=titulo)
        r += 1
        for fila in rubros[rubro]:
            _escribir_fila(sheet, r, fila["label"], fila["montos"], fila["pct"], consolidado)
            r += 1
        _escribir_fila(sheet, r, total_label, totales[rubro], pct_de(totales[rubro]), consolidado)
        r += 2

    # Net profit (subtotal derivado final)
    _escribir_fila(
        sheet, r, "NET PROFIT (OR LOSS)",
        totales["NET_PROFIT"], pct_de(totales["NET_PROFIT"]), consolidado,
    )


def _ajustar_columnas(sheet) -> None:
    for col in sheet.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            if cell.value is not None:
                max_len = max(max_len, len(str(cell.value)))
        sheet.column_dimensions[col_letter].width = min(max_len + 4, 60)


def escribir_pl(ruta_destino: str, plan: dict, periodo: str) -> None:
    wb = Workbook()
    consolidado = wb.active
    consolidado.title = "CONSOLIDATED"
    _escribir_hoja(consolidado, plan, periodo, consolidado=True)
    _ajustar_columnas(consolidado)

    por_segmento = wb.create_sheet("BY SEGMENT")
    _escribir_hoja(por_segmento, plan, periodo, consolidado=False)
    _ajustar_columnas(por_segmento)

    wb.save(ruta_destino)
