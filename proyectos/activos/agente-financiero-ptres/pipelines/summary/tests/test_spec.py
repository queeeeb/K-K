from pipelines.summary.spec import build_summary_spec

ESTRUCTURA_BASE = {"ledger_vivo": [], "cierres": [], "provisiones_actuales": []}


def _spec_estatico():
    return build_summary_spec(
        interpret_override=lambda raw_files: {},
        ruta_origen="estatico.xlsm",
        ruta_destino="salida_estatica.xlsm",
        hoja_mes_anterior="hoja_estatica_anterior",
        hoja_mes_nuevo="hoja_estatica_nueva",
    )


def test_calculate_usa_estatico_si_estructura_no_trae_datos_dinamicos():
    spec = _spec_estatico()

    plan = spec.calculate(ESTRUCTURA_BASE, estado_anterior=None)

    assert plan["detalle"]["ruta_origen"] == "estatico.xlsm"
    assert plan["detalle"]["hoja_mes_anterior"] == "hoja_estatica_anterior"
    assert plan["detalle"]["hoja_mes_nuevo"] == "hoja_estatica_nueva"


def test_calculate_prioriza_datos_dinamicos_de_estructura():
    spec = _spec_estatico()
    estructura = {
        **ESTRUCTURA_BASE,
        "ruta_base": "dinamico.xlsm",
        "hoja_mes_anterior": "2026_Jun",
        "hoja_mes_nuevo": "2026_Jul",
    }

    plan = spec.calculate(estructura, estado_anterior=None)

    assert plan["detalle"]["ruta_origen"] == "dinamico.xlsm"
    assert plan["detalle"]["hoja_mes_anterior"] == "2026_Jun"
    assert plan["detalle"]["hoja_mes_nuevo"] == "2026_Jul"


def _estructura_minima():
    return {
        "ledger_vivo": [
            {"proyecto": "26gmx3000.001", "anio": 2026, "periodo": "Abril", "monto_mxn": 1000,
             "cc": 3000, "cliente": "Cli", "nombre_proyecto": "N", "moneda": "MXN",
             "monto_original": 1000, "tc": 1},
        ],
        "cierres": [],
        "provisiones_actuales": [
            {"proyecto": "26gmx2000.005", "monto_mxn": 3000, "cc": 2000, "cliente": "Nuevo",
             "moneda": "MXN", "monto_original": 3000, "tc": 1},
        ],
        "concentrado": {3000: {"facturado": 1, "canceladas": 0}},
        "codigos_conocidos": {"26gmx3000.001"},
        "alertas": [],
        "hoja_mes_nuevo": "2026_May",
        "hoja_mes_anterior": "2026_Abr",
        "ruta_base": "irrelevante.xlsm",
    }


def test_spec_calculate_produce_grupos_ledger():
    spec = build_summary_spec(lambda *a, **k: {}, "o.xlsm", "d.xlsm", "2026_Abr", "2026_May")
    plan = spec.calculate(_estructura_minima(), estado_anterior=None)
    assert len(plan["resumen"]["mantenidas"]) == 1
    assert len(plan["resumen"]["nuevas"]) == 1
    assert plan["detalle"]["mes_actual"] == "May"
    assert plan["detalle"]["filas"][0][3] == "Abril"
    assert plan["detalle"]["filas"][-1][7] == "26gmx2000.005"
