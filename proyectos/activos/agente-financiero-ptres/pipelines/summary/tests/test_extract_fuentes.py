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


def test_extraer_ds_lee_codigo_monto_cliente_nombre_y_moneda_reales():
    rows = [
        ["Proyecto", "Cliente", "Nombre", "Moneda", "Mayo PROVISION"],
        ["26gmx7000.002", "Cliente Uno", "Soporte anual", "USD", 5000],
    ]
    estructura = {
        "provision_columna": 4, "codigo_columna": 0,
        "cliente_columna": 1, "nombre_columna": 2, "moneda_columna": 3, "fila_inicio_datos": 1,
    }

    resultado = extraer_ds(rows, estructura)

    assert resultado == [{
        "proyecto": "26gmx7000.002", "monto_mxn": 5000, "cc": 7000,
        "cliente": "Cliente Uno", "nombre_proyecto": "Soporte anual", "moneda": "USD",
    }]


def test_extraer_ds_sin_moneda_indicada_asume_mxn():
    rows = [
        ["Proyecto", "Cliente", "Nombre", "Moneda", "Mayo PROVISION"],
        ["26gmx7000.002", "Cliente Uno", "Soporte anual", None, 5000],
    ]
    estructura = {
        "provision_columna": 4, "codigo_columna": 0,
        "cliente_columna": 1, "nombre_columna": 2, "moneda_columna": 3, "fila_inicio_datos": 1,
    }

    resultado = extraer_ds(rows, estructura)

    assert resultado[0]["moneda"] == "MXN"


def test_extraer_ds_recorre_hasta_el_final_real_del_archivo():
    rows = [["Proyecto", "Cliente", "Nombre", "Mayo PROVISION"]] + [
        [f"26gmx3000.{i:03d}", "Cliente", "Nombre", 1000 + i] for i in range(1, 21)
    ]
    estructura = {
        "provision_columna": 3, "codigo_columna": 0,
        "cliente_columna": 1, "nombre_columna": 2, "fila_inicio_datos": 1,
    }

    resultado = extraer_ds(rows, estructura)

    assert len(resultado) == 20
    assert resultado[-1]["proyecto"] == "26gmx3000.020"


def test_extraer_ds_ignora_filas_con_codigo_vacio():
    rows = [
        ["Proyecto", "Cliente", "Nombre", "Mayo PROVISION"],
        ["26gmx7000.002", "Cliente Uno", "Nombre Uno", 5000],
        ["", None, None, None],
    ]
    estructura = {
        "provision_columna": 3, "codigo_columna": 0,
        "cliente_columna": 1, "nombre_columna": 2, "fila_inicio_datos": 1,
    }

    resultado = extraer_ds(rows, estructura)

    assert len(resultado) == 1


def test_extraer_ds_ignora_filas_con_codigo_no_texto():
    rows = [
        ["Proyecto", "Cliente", "Nombre", "Mayo PROVISION"],
        ["26gmx7000.002", "Cliente Uno", "Nombre Uno", 5000],
        [47832.19, "x", "y", 1000],
    ]
    estructura = {
        "provision_columna": 3, "codigo_columna": 0,
        "cliente_columna": 1, "nombre_columna": 2, "fila_inicio_datos": 1,
    }

    resultado = extraer_ds(rows, estructura)

    assert len(resultado) == 1


def test_extraer_ds_ignora_provision_en_cero_o_vacia():
    rows = [
        ["Proyecto", "Cliente", "Nombre", "Mayo PROVISION"],
        ["26gmx7000.002", "Cliente Uno", "Nombre Uno", 5000],
        ["26gmx7000.003", "Cliente Dos", "Nombre Dos", 0],
        ["26gmx7000.004", "Cliente Tres", "Nombre Tres", None],
        ["26gmx7000.005", "Cliente Cuatro", "Nombre Cuatro", -1.7e-12],
    ]
    estructura = {
        "provision_columna": 3, "codigo_columna": 0,
        "cliente_columna": 1, "nombre_columna": 2, "fila_inicio_datos": 1,
    }

    resultado = extraer_ds(rows, estructura)

    assert [r["proyecto"] for r in resultado] == ["26gmx7000.002"]


def test_extraer_ds_recorta_guion_y_espacios_colgantes_del_codigo():
    rows = [
        ["Proyecto", "Cliente", "Nombre", "Mayo PROVISION"],
        ["25gmx3000.118 - ", "Cliente Uno", "Nombre Uno", 5000],
    ]
    estructura = {
        "provision_columna": 3, "codigo_columna": 0,
        "cliente_columna": 1, "nombre_columna": 2, "fila_inicio_datos": 1,
    }

    resultado = extraer_ds(rows, estructura)

    assert resultado[0]["proyecto"] == "25gmx3000.118"


def test_extraer_ds_sin_cliente_ni_nombre_devuelve_vacios():
    rows = [
        ["Proyecto", "Cliente", "Nombre", "Mayo PROVISION"],
        ["26gmx7000.002", None, None, 5000],
    ]
    estructura = {
        "provision_columna": 3, "codigo_columna": 0,
        "cliente_columna": 1, "nombre_columna": 2, "fila_inicio_datos": 1,
    }

    resultado = extraer_ds(rows, estructura)

    assert resultado[0]["cliente"] == ""
    assert resultado[0]["nombre_proyecto"] == ""


def test_extraer_engineering_separa_codigo_y_cliente_y_lee_nombre():
    rows = [
        ["Categoria", "Nombre", "Proyecto", "Jan", "Feb", "Mar", "Apr", "May"],
        ["Project", "Nombre Descriptivo", "26gmx2000.005-Cliente Cuatro", 0, 0, 0, 0, 3000],
    ]
    estructura = {"mes_columna": 7, "codigo_columna": 2, "nombre_columna": 1, "fila_inicio_datos": 1}

    resultado = extraer_engineering(rows, estructura)

    assert resultado == [{
        "proyecto": "26gmx2000.005", "monto_mxn": 3000, "cc": 2000,
        "cliente": "Cliente Cuatro", "nombre_proyecto": "Nombre Descriptivo", "moneda": "MXN",
    }]


def test_extraer_engineering_ignora_mes_sin_valor():
    rows = [
        ["Categoria", "Nombre", "Proyecto", "Jan", "Feb", "Mar", "Apr", "May"],
        ["Project", "Nombre Uno", "26gmx2000.001-Cliente Uno", 100, 100, 100, None, None],
        ["Project", "Nombre Dos", "26gmx2000.002-Cliente Dos", 0, 0, 0, 0, 3000],
    ]
    estructura = {"mes_columna": 7, "codigo_columna": 2, "nombre_columna": 1, "fila_inicio_datos": 1}

    resultado = extraer_engineering(rows, estructura)

    assert [r["proyecto"] for r in resultado] == ["26gmx2000.002"]


def test_extraer_engineering_recorre_hasta_el_final_real_del_archivo():
    rows = [["Categoria", "Nombre", "Proyecto", "Jan", "Feb", "Mar", "Apr", "May"]] + [
        ["Project", f"Nombre {i}", f"26gmx2000.{i:03d}-Cliente {i}", 0, 0, 0, 0, 100 + i] for i in range(1, 21)
    ]
    estructura = {"mes_columna": 7, "codigo_columna": 2, "nombre_columna": 1, "fila_inicio_datos": 1}

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

    assert resultado == [{
        "proyecto": "26gmx3000.001", "cliente": "Cliente Uno", "nombre_proyecto": "Proyecto Uno",
        "monto_mxn": 600, "cc": 3000, "moneda": "MXN",
    }]


def test_extraer_consulting_suma_varias_filas_total_honorarios_del_mismo_bloque():
    rows = [
        ["STATUS", "PROJECT", "Consultor", "Total"],
        ["PROVISION", "26gmx3000.001\nCliente Uno\nProyecto Uno", "Total honorarios", 600],
        ["", "", "Total honorarios", 400],
    ]
    estructura = {"status_columna": 0, "project_columna": 1, "trigger_columna": 2, "monto_columna": 3}

    resultado = extraer_consulting(rows, estructura)

    assert resultado == [{
        "proyecto": "26gmx3000.001", "cliente": "Cliente Uno", "nombre_proyecto": "Proyecto Uno",
        "monto_mxn": 1000, "cc": 3000, "moneda": "MXN",
    }]


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

    assert resultado == [{
        "proyecto": "24gmx3000.075", "cliente": "BMW", "nombre_proyecto": "Proyecto X",
        "monto_mxn": 665280, "cc": 3000, "moneda": "MXN",
    }]


def test_extraer_consulting_descripcion_con_varias_lineas_se_une():
    rows = [
        ["STATUS", "PROJECT", "Consultor", "Total"],
        ["PROVISION", "25gmx3000.062\nBMW\nPMO support BP30.01\nTEM SLP", "Total honorarios", 100],
    ]
    estructura = {"status_columna": 0, "project_columna": 1, "trigger_columna": 2, "monto_columna": 3}

    resultado = extraer_consulting(rows, estructura)

    assert resultado[0]["nombre_proyecto"] == "PMO support BP30.01\nTEM SLP"


def test_extraer_consulting_acepta_trigger_con_descuento():
    rows = [
        ["STATUS", "PROJECT", "Consultor", "Total"],
        ["FACTURADO", "26gmx3000.079\nP3 USA\nBorgWarner", "Juan", 4517.92],
        ["", "", "Total honorarios con descuento 5%", 19269.432],
    ]
    estructura = {"status_columna": 0, "project_columna": 1, "trigger_columna": 2, "monto_columna": 3}

    resultado = extraer_consulting(rows, estructura)

    assert resultado == [{
        "proyecto": "26gmx3000.079", "cliente": "P3 USA", "nombre_proyecto": "BorgWarner",
        "monto_mxn": 19269.432, "cc": 3000, "moneda": "MXN",
    }]


def test_extraer_consulting_no_confunde_otro_texto_con_total_honorarios():
    rows = [
        ["STATUS", "PROJECT", "Consultor", "Total"],
        ["PROVISION", "26gmx3000.001\nCliente Uno\nProyecto Uno", "Gerardo", 500],
        ["", "", "Subtotal parcial", 999],
    ]
    estructura = {"status_columna": 0, "project_columna": 1, "trigger_columna": 2, "monto_columna": 3}

    resultado = extraer_consulting(rows, estructura)

    assert resultado[0]["monto_mxn"] == 0


def test_extraer_consulting_recorta_guion_colgante_del_codigo():
    rows = [
        ["STATUS", "PROJECT", "Consultor", "Total"],
        ["PROVISION", "25gmx3000.088 - \nP3 USA\nRIVIAN", "Total honorarios", 100],
    ]
    estructura = {"status_columna": 0, "project_columna": 1, "trigger_columna": 2, "monto_columna": 3}

    resultado = extraer_consulting(rows, estructura)

    assert resultado[0]["proyecto"] == "25gmx3000.088"


def test_extraer_consulting_sin_descripcion_devuelve_nombre_vacio():
    rows = [
        ["STATUS", "PROJECT", "Consultor", "Total"],
        ["PROVISION", "26gmx3000.001\nCliente Uno", "Total honorarios", 600],
    ]
    estructura = {"status_columna": 0, "project_columna": 1, "trigger_columna": 2, "monto_columna": 3}

    resultado = extraer_consulting(rows, estructura)

    assert resultado[0]["nombre_proyecto"] == ""


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
