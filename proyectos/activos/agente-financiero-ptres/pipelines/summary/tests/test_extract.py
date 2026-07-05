from openpyxl import Workbook

from pipelines.summary.extract import leer_provisiones_mes_anterior

HEADERS = ["Cotizacion", "Cierre", "Año", "Periodo", "CC", "Cliente", "Nombre Proyecto",
           "Proyecto", "Moneda", "Provision", "T/C Provision", "PROVISION MXN", "usd",
           "MXN", "EUR", "CAD", "TOTAL MXN", "Referencia", "Comentarios"]


def _wb_con_filas(filas: list[list]) -> Workbook:
    wb = Workbook()
    sheet = wb.active
    sheet.title = "2026_Abr"
    for col, header in enumerate(HEADERS, start=1):
        sheet.cell(row=12, column=col, value=header)
    for offset, fila in enumerate(filas, start=13):
        for col, valor in enumerate(fila, start=1):
            sheet.cell(row=offset, column=col, value=valor)
    return wb


def _fila(cierre, cc, cliente, proyecto, monto_mxn):
    return ["Q-1", cierre, 2026, "Abril", cc, cliente, "Nombre X", proyecto, "MXN",
            monto_mxn, 1, monto_mxn, 0, monto_mxn, 0, 0, monto_mxn, "", ""]


def test_leer_provisiones_incluye_solo_cierre_provision():
    wb = _wb_con_filas([
        _fila("Provision", 3000, "Cliente Uno", "26gmx3000.001", 1000),
        _fila("Cancelar", 7000, "Cliente Dos", "26gmx7000.002", 2000),
    ])

    resultado = leer_provisiones_mes_anterior(wb, "2026_Abr")

    assert len(resultado) == 1
    assert resultado[0]["proyecto"] == "26gmx3000.001"


def test_leer_provisiones_normaliza_espacio_en_cierre():
    wb = _wb_con_filas([
        _fila("Provision ", 3000, "Cliente Uno", "26gmx3000.001", 1000),
    ])

    resultado = leer_provisiones_mes_anterior(wb, "2026_Abr")

    assert len(resultado) == 1


def test_leer_provisiones_mapea_campos_esperados():
    wb = _wb_con_filas([
        _fila("Provision", 3000, "Cliente Uno", "26gmx3000.001", 17950),
    ])

    resultado = leer_provisiones_mes_anterior(wb, "2026_Abr")

    assert resultado[0] == {
        "proyecto": "26gmx3000.001",
        "monto_mxn": 17950,
        "cc": 3000,
        "cliente": "Cliente Uno",
    }


def test_leer_provisiones_ignora_filas_vacias():
    wb = _wb_con_filas([
        _fila("Provision", 3000, "Cliente Uno", "26gmx3000.001", 1000),
    ])
    # fila de nota suelta sin estructura, columna B vacía
    wb["2026_Abr"].cell(row=14, column=7, value="Se facturó junto con Mayo")

    resultado = leer_provisiones_mes_anterior(wb, "2026_Abr")

    assert len(resultado) == 1
