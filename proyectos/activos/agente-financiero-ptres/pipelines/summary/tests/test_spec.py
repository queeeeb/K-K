from pipelines.summary.spec import build_summary_spec

ESTRUCTURA_BASE = {"provisiones_mes_anterior": [], "facturas_mes": [], "provisiones_actuales": []}


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
