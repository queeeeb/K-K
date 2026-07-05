from pipelines.summary.extract_fuentes import (
    _cc_desde_codigo,
    extraer_consulting,
    extraer_ds,
    extraer_engineering,
    extraer_facturacion,
)


def test_cc_desde_codigo_acepta_los_3_segmentos_de_p3():
    assert _cc_desde_codigo("26gmx3000.001") == 3000
    assert _cc_desde_codigo("26gmx2000.005") == 2000
    assert _cc_desde_codigo("26gmx7000.002") == 7000


def test_cc_desde_codigo_rechaza_segmento_no_valido():
    assert _cc_desde_codigo("26gmx9999.001") is None


def test_extraer_ds_lee_codigo_y_monto_real():
    rows = [
        ["Proyecto", "Mayo PROVISION", "Mayo NUM.FACTURA"],
        ["26gmx7000.002", 5000, ""],
    ]
    estructura = {"provision_columna": 1, "codigo_columna": 0, "fila_inicio_datos": 1}

    resultado = extraer_ds(rows, estructura)

    assert resultado == [{"proyecto": "26gmx7000.002", "monto_mxn": 5000, "cc": 7000, "cliente": ""}]


def test_extraer_ds_recorre_hasta_el_final_real_del_archivo():
    rows = [["Proyecto", "Mayo PROVISION"]] + [
        [f"26gmx3000.{i:03d}", 1000 + i] for i in range(1, 21)
    ]
    estructura = {"provision_columna": 1, "codigo_columna": 0, "fila_inicio_datos": 1}

    resultado = extraer_ds(rows, estructura)

    assert len(resultado) == 20
    assert resultado[-1]["proyecto"] == "26gmx3000.020"


def test_extraer_ds_ignora_filas_con_codigo_vacio():
    rows = [
        ["Proyecto", "Mayo PROVISION"],
        ["26gmx7000.002", 5000],
        ["", None],
    ]
    estructura = {"provision_columna": 1, "codigo_columna": 0, "fila_inicio_datos": 1}

    resultado = extraer_ds(rows, estructura)

    assert len(resultado) == 1


def test_extraer_ds_ignora_filas_con_codigo_no_texto():
    rows = [
        ["Proyecto", "Mayo PROVISION"],
        ["26gmx7000.002", 5000],
        [47832.19, 1000],
    ]
    estructura = {"provision_columna": 1, "codigo_columna": 0, "fila_inicio_datos": 1}

    resultado = extraer_ds(rows, estructura)

    assert len(resultado) == 1


def test_extraer_engineering_separa_codigo_y_cliente():
    rows = [
        ["Proyecto", "Jan", "Feb", "Mar", "Apr", "May"],
        ["26gmx2000.005-Cliente Cuatro", 0, 0, 0, 0, 3000],
    ]
    estructura = {"mes_columna": 5, "codigo_columna": 0, "fila_inicio_datos": 1}

    resultado = extraer_engineering(rows, estructura)

    assert resultado == [
        {"proyecto": "26gmx2000.005", "monto_mxn": 3000, "cc": 2000, "cliente": "Cliente Cuatro"}
    ]


def test_extraer_engineering_recorre_hasta_el_final_real_del_archivo():
    rows = [["Proyecto", "Jan", "Feb", "Mar", "Apr", "May"]] + [
        [f"26gmx2000.{i:03d}-Cliente {i}", 0, 0, 0, 0, 100 + i] for i in range(1, 21)
    ]
    estructura = {"mes_columna": 5, "codigo_columna": 0, "fila_inicio_datos": 1}

    resultado = extraer_engineering(rows, estructura)

    assert len(resultado) == 20


def test_extraer_consulting_suma_las_filas_marcadas_total_honorarios():
    rows = [
        ["STATUS", "PROJECT", "Consultor", "Total"],
        ["PROVISION", "26gmx3000.001\nCliente Uno\nProyecto Uno", "Gerardo", 500],
        ["", "", "Total honorarios", 600],
        ["", "", "Elena", 100],
    ]
    estructura = {"status_columna": 0, "project_columna": 1, "trigger_columna": 2, "monto_columna": 3}

    resultado = extraer_consulting(rows, estructura)

    assert resultado == [
        {"proyecto": "26gmx3000.001", "cliente": "Cliente Uno", "monto_mxn": 600, "cc": 3000}
    ]


def test_extraer_consulting_suma_varias_filas_total_honorarios_del_mismo_bloque():
    rows = [
        ["STATUS", "PROJECT", "Consultor", "Total"],
        ["PROVISION", "26gmx3000.001\nCliente Uno\nProyecto Uno", "Total honorarios", 600],
        ["", "", "Total honorarios", 400],
    ]
    estructura = {"status_columna": 0, "project_columna": 1, "trigger_columna": 2, "monto_columna": 3}

    resultado = extraer_consulting(rows, estructura)

    assert resultado == [
        {"proyecto": "26gmx3000.001", "cliente": "Cliente Uno", "monto_mxn": 1000, "cc": 3000}
    ]


def test_extraer_consulting_ignora_status_distinto_de_provision_o_facturado():
    rows = [
        ["STATUS", "PROJECT", "Consultor", "Total"],
        ["CANCELADO", "26gmx3000.099\nCliente X\nProyecto X", "Total honorarios", 999],
    ]
    estructura = {"status_columna": 0, "project_columna": 1, "trigger_columna": 2, "monto_columna": 3}

    resultado = extraer_consulting(rows, estructura)

    assert resultado == []


def test_extraer_consulting_incluye_status_facturado():
    rows = [
        ["STATUS", "PROJECT", "Consultor", "Total"],
        ["FACTURADO", "24gmx3000.075\nBMW\nProyecto X", "Total honorarios", 665280],
    ]
    estructura = {"status_columna": 0, "project_columna": 1, "trigger_columna": 2, "monto_columna": 3}

    resultado = extraer_consulting(rows, estructura)

    assert resultado == [
        {"proyecto": "24gmx3000.075", "cliente": "BMW", "monto_mxn": 665280, "cc": 3000}
    ]


def test_extraer_facturacion_devuelve_proyecto_y_estado_crudos():
    rows = [
        ["Proyecto", "Estado"],
        ["26gmx3000.001-Cliente Uno- Proyecto Uno", "Pagado"],
        ["26gmx7000.099-Cliente Tres- Proyecto Tres", "Sin pagar"],
    ]
    estructura = {"proyecto_columna": 0, "estado_columna": 1}

    resultado = extraer_facturacion(rows, estructura)

    assert resultado == [
        {"proyecto": "26gmx3000.001-Cliente Uno- Proyecto Uno", "estado": "Pagado"},
        {"proyecto": "26gmx7000.099-Cliente Tres- Proyecto Tres", "estado": "Sin pagar"},
    ]
