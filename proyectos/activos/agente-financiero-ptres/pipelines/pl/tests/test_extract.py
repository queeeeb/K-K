from openpyxl import Workbook

from pipelines.pl.extract import extraer


def _ws(filas):
    wb = Workbook()
    ws = wb.active
    for i, celdas in enumerate(filas, start=1):
        for col, val in celdas.items():
            ws.cell(row=i, column=col, value=val)
    return ws


def test_extraer_cuentas_con_total_seg():
    ws = _ws([
        {1: "6100-001-001-000", 2: "SUELDOS Y SALARIOS"},
        {1: "Segmento:    2 ING"},
        {5: "Total Seg. ING:", 6: 400, 7: 0},
    ])
    resultado = extraer(ws)
    cuentas = resultado["cuentas"]
    assert len(cuentas) == 1
    assert cuentas[0]["numero"] == "6100-001-001-000"
    assert cuentas[0]["segmentos"]["ING"] == {"cargos": 400, "abonos": 0}


def test_ventas_nacionales_se_desglosan_por_cliente_y_segmento():
    ws = _ws([
        {1: "4110-001-001-000", 2: "VENTAS NACIONALES"},
        {1: "Segmento:    2 ING"},
        {1: "31/Mar/2026", 2: "Diario", 4: "FORD MOTOR COMPANY", 7: 1000},
        {1: "31/Mar/2026", 2: "Diario", 4: "FORD MOTOR COMPANY", 7: 500},
        {1: "31/Mar/2026", 2: "Diario", 4: "SCOTIABANK INVERLAT", 7: 300},
        {5: "Total Seg. ING:", 6: 0, 7: 1800},
    ])
    ns = extraer(ws)["ventas_nacionales"]
    # FORD acumula 1000+500 en ING; SCOTIA 300 en ING
    assert {"cliente": "FORD MOTOR COMPANY", "segmento": "ING", "monto": 1500.0} in ns
    assert {"cliente": "SCOTIABANK INVERLAT", "segmento": "ING", "monto": 300.0} in ns
    assert len(ns) == 2


def test_ventas_nacionales_solo_dentro_del_lump_sum():
    # Un Diario fuera de 4110-001-001-000 no debe contar como venta nacional
    ws = _ws([
        {1: "4110-002-001-000", 2: "FORD MOTOR COMPANY"},
        {1: "Segmento:    2 ING"},
        {1: "31/Mar/2026", 2: "Diario", 4: "OTRO", 7: 999},
        {5: "Total Seg. ING:", 6: 0, 7: 999},
    ])
    assert extraer(ws)["ventas_nacionales"] == []
