from pipelines.summary.calculate import (
    actualizar_nombres_nuevas,
    cruzar_cierres,
    extraer_codigo,
    normalizar_codigo,
    reconciliar,
)


def test_cruzar_cierres_par_en_ambas_sin_alerta():
    cierres, alertas = cruzar_cierres(
        pares_facturacion=[("26gmx7000.010", 2026, "Marzo")],
        pares_notas_ds=[("26gmx7000.010", 2026, "Marzo")],
    )
    assert cierres == [{"codigo": "26gmx7000.010", "anio": 2026, "mes": "Marzo", "origen": "ambas"}]
    assert alertas == []


def test_cruzar_cierres_par_solo_facturacion_cierra_sin_alerta():
    cierres, alertas = cruzar_cierres(
        pares_facturacion=[("26gmx3000.001", 2026, "Abril")],
        pares_notas_ds=[],
    )
    assert cierres[0]["origen"] == "facturacion"
    assert alertas == []


def test_cruzar_cierres_par_solo_notas_ds_cierra_sin_alerta():
    cierres, alertas = cruzar_cierres(
        pares_facturacion=[],
        pares_notas_ds=[("26gmx7000.010", 2026, "Marzo")],
    )
    assert cierres[0]["origen"] == "notas_ds"
    assert alertas == []


def test_extraer_codigo_limpio():
    assert extraer_codigo("26gmx7000.002", formato="limpio") == "26gmx7000.002"


def test_extraer_codigo_guion():
    assert extraer_codigo("26gmx3000.001-Cliente Uno- Proyecto Uno", formato="guion") == "26gmx3000.001"


def test_extraer_codigo_multilinea():
    assert extraer_codigo("26gmx3000.001\nCliente Uno\nProyecto Uno", formato="multilinea") == "26gmx3000.001"


def test_extraer_codigo_guion_con_descripcion_por_espacio():
    assert extraer_codigo("26gmx7000.000156 Cloud", formato="guion") == "26gmx7000.000156"


def test_normalizar_codigo_corta_descripcion_por_espacio():
    assert normalizar_codigo("26gmx7000.000156 Cloud") == "26gmx7000.000156"
    assert normalizar_codigo("25gmx7000.S02445 Architecture Service") == "25gmx7000.S02445"


def test_normalizar_codigo_corta_descripcion_por_guion():
    assert normalizar_codigo("26gmx2000.003-VW Ingenieria") == "26gmx2000.003"
    assert normalizar_codigo("26gmx7000.S02671-FP CCOP 2026") == "26gmx7000.S02671"


def test_normalizar_codigo_mezcla_espacio_y_guion():
    assert normalizar_codigo("26gmx7000.S02894 FP-PM Support") == "26gmx7000.S02894"


def test_normalizar_codigo_elimina_espacio_tras_punto():
    assert normalizar_codigo("26gmx7000. S02968 FP Reportes 2026") == "26gmx7000.S02968"


def test_normalizar_codigo_deja_intacto_codigo_limpio():
    assert normalizar_codigo("26gmx2000.013") == "26gmx2000.013"


def test_normalizar_codigo_no_toca_formato_invalido():
    assert normalizar_codigo("24gxm3000.037") == "24gxm3000.037"


def _fila_ledger(proyecto, anio, periodo, monto=1000, cc=3000):
    return {"proyecto": proyecto, "anio": anio, "periodo": periodo, "monto_mxn": monto,
            "cc": cc, "cliente": "Cliente X", "nombre_proyecto": "N", "moneda": "MXN",
            "monto_original": monto, "tc": 1}


def test_reconciliar_mantiene_fila_no_cerrada_intacta():
    ledger = [_fila_ledger("26gmx3000.001", 2026, "Marzo", monto=1500)]
    resultado = reconciliar(ledger, cierres=[], provisiones_actuales=[])
    assert resultado["mantenidas"] == ledger
    assert resultado["cerradas"] == []


def test_reconciliar_cierra_fila_por_codigo_y_periodo():
    ledger = [
        _fila_ledger("26gmx3000.001", 2026, "Marzo"),
        _fila_ledger("26gmx3000.001", 2026, "Abril"),
    ]
    cierres = [{"codigo": "26gmx3000.001", "anio": 2026, "mes": "Marzo", "origen": "ambas"}]
    resultado = reconciliar(ledger, cierres, provisiones_actuales=[])
    assert len(resultado["cerradas"]) == 1
    assert resultado["cerradas"][0]["periodo"] == "Marzo"
    assert len(resultado["mantenidas"]) == 1
    assert resultado["mantenidas"][0]["periodo"] == "Abril"


def test_reconciliar_cierre_codigo_ausente_es_informativo():
    ledger = [_fila_ledger("26gmx3000.001", 2026, "Marzo")]
    cierres = [{"codigo": "26gmx9999.999", "anio": 2026, "mes": "Marzo", "origen": "facturacion"}]
    resultado = reconciliar(ledger, cierres, provisiones_actuales=[])
    assert resultado["cerradas"] == []
    assert len(resultado["mantenidas"]) == 1
    alerta = next(a for a in resultado["alertas"] if "26gmx9999.999" in a)
    assert "sin provisión previa" in alerta
    assert "informativo" in alerta
    assert "requiere revisión manual" not in alerta


def test_reconciliar_cierre_codigo_presente_sin_casar_periodo_requiere_revision():
    ledger = [_fila_ledger("26gmx3000.001", 2026, "Marzo")]
    cierres = [{"codigo": "26gmx3000.001", "anio": 2026, "mes": "Abril", "origen": "facturacion"}]
    resultado = reconciliar(ledger, cierres, provisiones_actuales=[])
    assert resultado["cerradas"] == []
    assert len(resultado["mantenidas"]) == 1
    alerta = next(a for a in resultado["alertas"] if "26gmx3000.001" in a)
    assert "no casó" in alerta
    assert "requiere revisión manual" in alerta


def test_reconciliar_provision_actual_es_fila_nueva_aunque_codigo_exista():
    ledger = [_fila_ledger("26gmx3000.001", 2026, "Marzo")]
    actuales = [{"proyecto": "26gmx3000.001", "monto_mxn": 2000, "cc": 3000, "cliente": "Cliente X"}]
    resultado = reconciliar(ledger, cierres=[], provisiones_actuales=actuales,
                            codigos_conocidos={"26gmx3000.001"})
    assert len(resultado["mantenidas"]) == 1
    assert len(resultado["nuevas"]) == 1
    assert resultado["nuevas"][0]["codigo_nuevo"] is False


def test_reconciliar_detecta_provision_nueva():
    resultado = reconciliar(
        ledger_vivo=[],
        cierres=[],
        provisiones_actuales=[{"proyecto": "26gmx2000.005", "monto_mxn": 3000, "cc": 2000, "cliente": "Cliente Cuatro"}],
    )

    assert resultado["nuevas"][0]["proyecto"] == "26gmx2000.005"


def test_reconciliar_marca_codigo_nunca_visto_como_nuevo():
    resultado = reconciliar(
        ledger_vivo=[],
        cierres=[],
        provisiones_actuales=[{"proyecto": "26gmx2000.005", "monto_mxn": 3000, "cc": 2000, "cliente": "Cliente Cuatro"}],
        codigos_conocidos={"26gmx3000.001"},
    )

    assert resultado["nuevas"][0]["codigo_nuevo"] is True


def test_reconciliar_no_marca_codigo_ya_conocido():
    resultado = reconciliar(
        ledger_vivo=[],
        cierres=[],
        provisiones_actuales=[{"proyecto": "26gmx2000.005", "monto_mxn": 3000, "cc": 2000, "cliente": "Cliente Cuatro"}],
        codigos_conocidos={"26gmx2000.005"},
    )

    assert resultado["nuevas"][0]["codigo_nuevo"] is False


def test_reconciliar_sin_codigos_conocidos_marca_todo_como_nuevo():
    resultado = reconciliar(
        ledger_vivo=[],
        cierres=[],
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


def test_reconciliar_incluye_alertas_vacias_por_defecto():
    resultado = reconciliar([], [], [])
    assert resultado["alertas"] == []


def test_reconciliar_acepta_alertas():
    alertas = ["Proyecto sin código en DS — fila 24."]
    resultado = reconciliar([], [], [], alertas=alertas)
    assert resultado["alertas"] == alertas
