"""Escritura determinista del P&L con openpyxl: hojas CONSOLIDATED y BY SEGMENT,
siguiendo el orden de secciones y el catálogo de labels de la referencia (macro).
No decide nada — solo vuelca el plan. Ver ESPECIFICACION §2 y §5.
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from pipelines.pl import referencia
from pipelines.pl.calculate import COLUMNAS_SALIDA, SEGMENTOS, safe_pct

ETIQUETAS_SEGMENTO = ["BACK OFFICE", "CONSUL OP", "ENGINEERING", "DIGITAL SOLUTIONS"]
FMT_MONTO = "#,##0.00"
FMT_PCT = "0.00%"

_CEROS = {col: 0.0 for col in COLUMNAS_SALIDA}
_FILL_TITULO = PatternFill("solid", fgColor="99CCFF")
_FILL_HEADER = PatternFill("solid", fgColor="800000")
_FONT_HEADER = Font(bold=True, color="FFFFFF")


def _agrupar_por_label(filas) -> dict:
    acumulado: dict = {}
    for fila in filas:
        montos = acumulado.setdefault(fila["label"], {col: 0.0 for col in COLUMNAS_SALIDA})
        for col in COLUMNAS_SALIDA:
            montos[col] += fila["montos"][col]
    return acumulado


def _escribir_fila(sheet, r, label, montos, base, consolidado):
    sheet.cell(row=r, column=1, value=label)

    def celda(col_monto, col_pct, valor):
        if valor == 0:
            sheet.cell(row=r, column=col_monto, value="-")
            sheet.cell(row=r, column=col_pct, value="-")
        else:
            c = sheet.cell(row=r, column=col_monto, value=valor)
            c.number_format = FMT_MONTO

    def celda_pct(col_pct, valor, base_col):
        if valor != 0:
            c = sheet.cell(row=r, column=col_pct, value=safe_pct(valor, base_col))
            c.number_format = FMT_PCT

    if consolidado:
        celda(2, 3, montos["TOTAL"])
        celda_pct(3, montos["TOTAL"], base["TOTAL"])
    else:
        for i, seg in enumerate(SEGMENTOS):
            celda(2 + i * 2, 3 + i * 2, montos[seg])
            celda_pct(3 + i * 2, montos[seg], base[seg])
        celda(10, 11, montos["TOTAL"])
        celda_pct(11, montos["TOTAL"], base["TOTAL"])


def _escribir_hoja(sheet, plan, periodo, consolidado):
    base = plan["base_ingresos"]
    totales = plan["totales"]
    rubros = plan["rubros"]
    alloc = plan["allocations"]
    ncols = 3 if consolidado else 11

    def fila(label, montos):
        nonlocal r
        _escribir_fila(sheet, r, label, montos, base, consolidado)
        r += 1

    def titulo(texto):
        nonlocal r
        c = sheet.cell(row=r, column=1, value=texto)
        c.font = Font(bold=True)
        r += 1

    def barra(label, montos, fill, blanco=False):
        nonlocal r
        _escribir_fila(sheet, r, label, montos, base, consolidado)
        for col in range(1, ncols + 1):
            celda = sheet.cell(row=r, column=col)
            celda.fill = fill
            celda.font = Font(bold=True, color="FFFFFF" if blanco else "000000")
        r += 1

    r = 1
    sheet.cell(row=r, column=1, value="P-TRES GROUP, S.A.P.I. DE C.V.").font = Font(bold=True, size=12)
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
    for col in range(1, ncols + 1):
        sheet.cell(row=r, column=col).font = _FONT_HEADER
        sheet.cell(row=r, column=col).fill = _FILL_HEADER
    r += 1

    incomes = rubros["INCOMES"]
    ns = _agrupar_por_label([f for f in incomes if f["grupo"] == referencia.GRUPO_VENTAS_NACIONALES])
    accrued = _agrupar_por_label([f for f in incomes if f["numero"][:8] in ("4110-004", "4110-005")])
    internacionales = [f for f in incomes if f["numero"][:8] == "4110-002" and f["montos"]["TOTAL"] != 0]

    titulo("Incomes")
    titulo("  NATIONAL SALES")
    for cliente in referencia.CATALOGO_NATIONAL_SALES:
        fila("    " + cliente, ns.get(cliente, _CEROS))
    for f in internacionales:
        fila(f["label"], f["montos"])
    for label in referencia.CATALOGO_ACCRUED_REVENUE:
        fila(label, accrued.get(label, _CEROS))
    barra("Incomes Total", totales["INCOMES"], _FILL_TITULO)
    r += 1

    exp = _agrupar_por_label(rubros["EXPENSES"])
    titulo("Expenses")
    for label in referencia.CATALOGO_EXPENSES:
        fila(label, exp.get(label, _CEROS))
    barra("Expenses Total", totales["EXPENSES"], _FILL_TITULO)
    r += 1

    barra("OPERATING PROFIT (OR LOSS) BEFORE ALLOCATIONS", totales["OPERATING_PROFIT"], _FILL_TITULO)
    r += 1

    if not consolidado:
        titulo("ALLOCATION BO & GMBH SERVICES")
        fila("P3 GLOBAL GMBH SERVICES", alloc["gmbh"])
        fila("  ALLOCATION OF BACK OFFICE - EXPENSES", alloc["back_office"])
        barra("OPERATING PROFIT (OR LOSS) - After Allocation",
              totales["OPERATING_AFTER_ALLOCATION"], _FILL_HEADER, blanco=True)
        r += 1

    for titulo_sec, rubro, total_label, catalogo in [
        ("Other Incomes", "OTHER_INCOMES", "Other Incomes Total", referencia.CATALOGO_OTHER_INCOMES),
        ("Other Expenses", "OTHER_EXPENSES", "Other Expenses Total", referencia.CATALOGO_OTHER_EXPENSES),
        ("Accrued Taxes", "ACCRUED_TAXES", "Accrued Taxes Total", referencia.CATALOGO_ACCRUED_TAXES),
    ]:
        agrupado = _agrupar_por_label(rubros[rubro])
        titulo(titulo_sec)
        for label in catalogo:
            fila(label, agrupado.get(label, _CEROS))
        barra(total_label, totales[rubro], _FILL_TITULO)
        r += 1

    barra("NET PROFIT (OR LOSS)", totales["NET_PROFIT"], _FILL_HEADER, blanco=True)


def _ajustar_columnas(sheet) -> None:
    for col in sheet.columns:
        col_letter = col[0].column_letter
        max_len = max((len(str(c.value)) for c in col if c.value is not None), default=0)
        sheet.column_dimensions[col_letter].width = min(max_len + 4, 55)


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
