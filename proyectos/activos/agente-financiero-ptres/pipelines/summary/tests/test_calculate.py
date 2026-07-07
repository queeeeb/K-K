from pipelines.summary.calculate import (
    actualizar_nombres_nuevas,
    cruzar_cierres,
    extraer_codigo,
    reconciliar,
)


def test_cruzar_cierres_par_en_ambas_sin_alerta():
    cierres, alertas = cruzar_cierres(
        pares_facturacion=[("26gmx7000.010", 2026, "Marzo")],
        pares_notas_ds=[("26gmx7000.010", 2026, "Marzo")],
    )
    assert cierres == [{"codigo": "26gmx7000.010", "anio": 2026, "mes": "Marzo", "origen": "ambas"}]
    assert alertas == []


def test_cruzar_cierres_par_solo_facturacion_cierra_con_alerta():
    cierres, alertas = cruzar_cierres(
        pares_facturacion=[("26gmx3000.001", 2026, "Abril")],
        pares_notas_ds=[],
    )
    assert cierres[0]["origen"] == "facturacion"
    assert any("solo" in a.lower() and "facturaci" in a.lower() for a in alertas)


def test_cruzar_cierres_par_solo_notas_ds_cierra_con_alerta():
    cierres, alertas = cruzar_cierres(
        pares_facturacion=[],
        pares_notas_ds=[("26gmx7000.010", 2026, "Marzo")],
    )
    assert cierres[0]["origen"] == "notas_ds"
    assert any("solo" in a.lower() and "notas" in a.lower() for a in alertas)


def test_extraer_codigo_limpio():
    assert extraer_codigo("26gmx7000.002", formato="limpio") == "26gmx7000.002"


def test_extraer_codigo_guion():
    assert extraer_codigo("26gmx3000.001-Cliente Uno- Proyecto Uno", formato="guion") == "26gmx3000.001"


def test_extraer_codigo_multilinea():
    assert extraer_codigo("26gmx3000.001\nCliente Uno\nProyecto Uno", formato="multilinea") == "26gmx3000.001"


def test_reconciliar_cancela_proyecto_facturado():
    provisiones_anteriores = [{"proyecto": "26gmx3000.001", "monto_mxn": 1000, "cc": 3000, "cliente": "Cliente Uno"}]
    facturas = [{"proyecto": "26gmx3000.001-Cliente Uno- Proyecto Uno", "estado": "Pagado"}]

    resultado = reconciliar(provisiones_anteriores, facturas, provisiones_actuales=[])

    assert len(resultado["canceladas"]) == 1
    assert resultado["canceladas"][0]["proyecto"] == "26gmx3000.001"
    assert resultado["activas"] == []


def test_reconciliar_factura_cancelada_no_cuenta():
    provisiones_anteriores = [{"proyecto": "26gmx3000.001", "monto_mxn": 1000, "cc": 3000, "cliente": "Cliente Uno"}]
    facturas = [{"proyecto": "26gmx3000.001-Cliente Uno- Proyecto Uno", "estado": "Cancelado"}]

    resultado = reconciliar(provisiones_anteriores, facturas, provisiones_actuales=[])

    assert resultado["activas"][0]["proyecto"] == "26gmx3000.001"
    assert resultado["canceladas"] == []


def test_reconciliar_detecta_provision_nueva():
    resultado = reconciliar(
        provisiones_mes_anterior=[],
        facturas_mes=[],
        provisiones_actuales=[{"proyecto": "26gmx2000.005", "monto_mxn": 3000, "cc": 2000, "cliente": "Cliente Cuatro"}],
    )

    assert resultado["nuevas"][0]["proyecto"] == "26gmx2000.005"


def test_reconciliar_marca_codigo_nunca_visto_como_nuevo():
    resultado = reconciliar(
        provisiones_mes_anterior=[],
        facturas_mes=[],
        provisiones_actuales=[{"proyecto": "26gmx2000.005", "monto_mxn": 3000, "cc": 2000, "cliente": "Cliente Cuatro"}],
        codigos_conocidos={"26gmx3000.001"},
    )

    assert resultado["nuevas"][0]["codigo_nuevo"] is True


def test_reconciliar_no_marca_codigo_ya_conocido():
    resultado = reconciliar(
        provisiones_mes_anterior=[],
        facturas_mes=[],
        provisiones_actuales=[{"proyecto": "26gmx2000.005", "monto_mxn": 3000, "cc": 2000, "cliente": "Cliente Cuatro"}],
        codigos_conocidos={"26gmx2000.005"},
    )

    assert resultado["nuevas"][0]["codigo_nuevo"] is False


def test_reconciliar_sin_codigos_conocidos_marca_todo_como_nuevo():
    resultado = reconciliar(
        provisiones_mes_anterior=[],
        facturas_mes=[],
        provisiones_actuales=[{"proyecto": "26gmx2000.005", "monto_mxn": 3000, "cc": 2000, "cliente": "Cliente Cuatro"}],
    )

    assert resultado["nuevas"][0]["codigo_nuevo"] is True


def _plan_con_nueva_sin_nombre():
    return {
        "resumen": {
            "canceladas": [], "activas": [],
            "nuevas": [{"proyecto": "26gmx2000.005", "monto_mxn": 3000, "cc": 2000, "cliente": "", "codigo_nuevo": True}],
            "alertas": [],
        },
        "detalle": {
            "filas": [
                ["", "Provision", 2026, "Mayo", 2000, "", "", "26gmx2000.005", "MXN", 3000, 1, 3000, 0, 3000, 0, 0, 3000, "", ""],
            ],
            "counts": {"canceladas": 0, "activas": 0, "nuevas": 1},
        },
    }


def test_actualizar_nombres_nuevas_actualiza_resumen_y_fila():
    plan = _plan_con_nueva_sin_nombre()

    resultado = actualizar_nombres_nuevas(plan, {"26gmx2000.005": "Cliente Cuatro"})

    assert resultado["resumen"]["nuevas"][0]["cliente"] == "Cliente Cuatro"
    assert resultado["resumen"]["nuevas"][0]["codigo_nuevo"] is False
    assert resultado["detalle"]["filas"][0][5] == "Cliente Cuatro"


def test_actualizar_nombres_nuevas_ignora_codigos_no_mencionados():
    plan = _plan_con_nueva_sin_nombre()

    resultado = actualizar_nombres_nuevas(plan, {"26gmx9999.999": "Otro Cliente"})

    assert resultado["resumen"]["nuevas"][0]["cliente"] == ""
    assert resultado["resumen"]["nuevas"][0]["codigo_nuevo"] is True


def test_reconciliar_activas_tienen_monto_anterior():
    provisiones_anteriores = [{"proyecto": "26gmx3000.001", "monto_mxn": 1500, "cc": 3000, "cliente": "Cliente Uno"}]
    facturas = []

    resultado = reconciliar(provisiones_anteriores, facturas, provisiones_actuales=[])

    assert resultado["activas"][0]["monto_mxn_anterior"] == 1500
    assert resultado["activas"][0]["monto_mxn"] == 1500


def test_reconciliar_actualiza_monto_de_activa_encontrada_en_fuentes():
    provisiones_anteriores = [{"proyecto": "26gmx3000.001", "monto_mxn": 1000, "cc": 3000, "cliente": "Cliente Uno"}]
    provisiones_actuales = [{"proyecto": "26gmx3000.001", "monto_mxn": 1800, "cc": 3000, "cliente": "Cliente Uno"}]

    resultado = reconciliar(provisiones_anteriores, facturas_mes=[], provisiones_actuales=provisiones_actuales)

    assert resultado["activas"][0]["monto_mxn"] == 1800
    assert resultado["activas"][0]["monto_mxn_anterior"] == 1000


def test_reconciliar_activa_toma_moneda_y_tc_del_mes_actual():
    provisiones_anteriores = [{"proyecto": "26gmx7000.002", "monto_mxn": 17950, "cc": 7000, "cliente": "Cliente Uno", "moneda": "USD", "monto_original": 1000, "tc": 17.95}]
    provisiones_actuales = [{"proyecto": "26gmx7000.002", "monto_mxn": 18130, "cc": 7000, "cliente": "Cliente Uno", "moneda": "USD", "monto_original": 1000, "tc": 18.13}]

    resultado = reconciliar(provisiones_anteriores, facturas_mes=[], provisiones_actuales=provisiones_actuales)

    activa = resultado["activas"][0]
    assert activa["moneda"] == "USD"
    assert activa["monto_original"] == 1000
    assert activa["tc"] == 18.13
    assert activa["monto_mxn"] == 18130


def test_reconciliar_no_duplica_activa_encontrada_como_nueva():
    provisiones_anteriores = [{"proyecto": "26gmx3000.001", "monto_mxn": 1000, "cc": 3000, "cliente": "Cliente Uno"}]
    provisiones_actuales = [{"proyecto": "26gmx3000.001", "monto_mxn": 1800, "cc": 3000, "cliente": "Cliente Uno"}]

    resultado = reconciliar(provisiones_anteriores, facturas_mes=[], provisiones_actuales=provisiones_actuales)

    assert resultado["nuevas"] == []


def test_reconciliar_activa_no_encontrada_en_fuentes_mantiene_monto_y_alerta():
    provisiones_anteriores = [{"proyecto": "26gmx3000.001", "monto_mxn": 1000, "cc": 3000, "cliente": "Cliente Uno"}]

    resultado = reconciliar(provisiones_anteriores, facturas_mes=[], provisiones_actuales=[])

    assert resultado["activas"][0]["monto_mxn"] == 1000
    assert any("26gmx3000.001" in alerta for alerta in resultado["alertas"])


def test_reconciliar_incluye_alertas_vacias_por_defecto():
    resultado = reconciliar([], [], [])
    assert resultado["alertas"] == []


def test_reconciliar_acepta_alertas():
    alertas = ["Proyecto sin código en DS — fila 24."]
    resultado = reconciliar([], [], [], alertas=alertas)
    assert resultado["alertas"] == alertas
