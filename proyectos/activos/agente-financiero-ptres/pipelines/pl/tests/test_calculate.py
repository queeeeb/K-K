from pipelines.pl.calculate import (
    calcular_pl,
    es_ingreso,
    monto_neto,
    safe_pct,
)
from pipelines.pl.referencia import clasificar_por_numero


def test_es_ingreso_por_prefijo():
    assert es_ingreso("4110-002-001-000") is True
    assert es_ingreso("6100-001-001-000") is False
    assert es_ingreso("8000-001-000-000") is False


def test_monto_neto_aplica_signo_segun_tipo():
    assert monto_neto(cargos=0, abonos=1000, ingreso=True) == 1000
    assert monto_neto(cargos=400, abonos=0, ingreso=False) == 400
    # un ingreso con cargos resta; un gasto con abonos resta
    assert monto_neto(cargos=100, abonos=1000, ingreso=True) == 900
    assert monto_neto(cargos=400, abonos=50, ingreso=False) == 350


def test_safe_pct_base_cero():
    assert safe_pct(100, 0) == 0.0
    assert safe_pct(400, 1000) == 0.4


def test_clasificar_por_numero_referencia():
    assert clasificar_por_numero("4110-001-001-000") == ("4110", "INCOMES")
    assert clasificar_por_numero("4210-001-000-000") == ("4210", "OTHER_INCOMES")
    assert clasificar_por_numero("6100-001-001-000") == ("6001", "EXPENSES")
    assert clasificar_por_numero("6100-009-001-000") == ("6009", "OTHER_EXPENSES")
    assert clasificar_por_numero("8000-001-000-000") == ("8000", "ACCRUED_TAXES")
    assert clasificar_por_numero("9999-000-000-000") == ("", "")


def _cuentas_demo():
    return [
        {"numero": "4110-002-001-000", "label": "  FORD", "rubro": "INCOMES",
         "segmentos": {"ING": {"cargos": 0, "abonos": 1000}}},
        {"numero": "6100-001-001-000", "label": "  GENERAL DEP", "rubro": "EXPENSES",
         "segmentos": {"ING": {"cargos": 400, "abonos": 0}}},
        {"numero": "4210-001-000-000", "label": "  E.R. FLUCTUATION PROFIT", "rubro": "OTHER_INCOMES",
         "segmentos": {"ING": {"cargos": 0, "abonos": 50}}},
        {"numero": "6100-009-001-000", "label": "  E.R. FLUCTUATION LOSS", "rubro": "OTHER_EXPENSES",
         "segmentos": {"ING": {"cargos": 20, "abonos": 0}}},
        {"numero": "8000-001-000-000", "label": "  INCOME TAX OF THE YEAR", "rubro": "ACCRUED_TAXES",
         "segmentos": {"ING": {"cargos": 10, "abonos": 0}}},
    ]


def test_calcular_pl_subtotales_y_net_profit():
    plan = calcular_pl(_cuentas_demo())
    totales = plan["totales"]

    assert totales["INCOMES"]["ING"] == 1000
    assert totales["EXPENSES"]["ING"] == 400
    assert totales["OPERATING_PROFIT"]["ING"] == 600
    assert totales["OTHER_INCOMES"]["ING"] == 50
    assert totales["OTHER_EXPENSES"]["ING"] == 20
    assert totales["ACCRUED_TAXES"]["ING"] == 10
    # NET = 600 + 50 - 20 - 10
    assert totales["NET_PROFIT"]["ING"] == 620
    assert totales["NET_PROFIT"]["TOTAL"] == 620


def test_calcular_pl_base_excluye_lump_sum():
    cuentas = _cuentas_demo() + [
        {"numero": "4110-001-001-000", "label": "NATIONAL SALES (lump)", "rubro": "INCOMES",
         "segmentos": {"ING": {"cargos": 0, "abonos": 99999}}},
    ]
    plan = calcular_pl(cuentas)
    # la cuenta lump-sum NO entra en la base de %
    assert plan["base_ingresos"]["ING"] == 1000
    # pero sí suma al total de INCOMES
    assert plan["totales"]["INCOMES"]["ING"] == 100999


def test_calcular_pl_porcentaje_sobre_base():
    plan = calcular_pl(_cuentas_demo())
    fila_gasto = next(f for f in plan["rubros"]["EXPENSES"] if f["numero"] == "6100-001-001-000")
    assert fila_gasto["pct"]["ING"] == 0.4


def _cuentas_allocation():
    return [
        {"numero": "4110-002-001-000", "label": "CONS", "rubro": "INCOMES", "grupo": "4110",
         "segmentos": {"CONS OPS": {"cargos": 0, "abonos": 100}}},
        {"numero": "4110-002-002-000", "label": "ENG", "rubro": "INCOMES", "grupo": "4110",
         "segmentos": {"ING": {"cargos": 0, "abonos": 300}}},
        {"numero": "4110-002-003-000", "label": "DS", "rubro": "INCOMES", "grupo": "4110",
         "segmentos": {"DIGITAL SOLUTIONS": {"cargos": 0, "abonos": 600}}},
        {"numero": "6100-007-050-000", "label": "  P3 GLOBAL GMBH SERVICES", "rubro": "EXPENSES",
         "grupo": "6007", "segmentos": {"BO": {"cargos": 200, "abonos": 0}}},
        {"numero": "6100-006-001-000", "label": "  TELEPHONE", "rubro": "EXPENSES", "grupo": "6006",
         "segmentos": {"BO": {"cargos": 300, "abonos": 0}}},
    ]


def test_allocations_convencion_vf_final():
    plan = calcular_pl(_cuentas_allocation())
    # GMBH se saca de Expenses: solo queda el otro gasto de BO (300)
    assert plan["totales"]["EXPENSES"]["BO"] == 300
    assert plan["totales"]["EXPENSES"]["TOTAL"] == 300
    assert not any(f["label"] == "  P3 GLOBAL GMBH SERVICES" for f in plan["rubros"]["EXPENSES"])

    al = plan["allocations"]
    # GMBH (200): BO positivo, y a CONS/ING/DS por % de ingreso (100/300/600 de 1000)
    assert al["gmbh"]["BO"] == 200
    assert al["gmbh"]["CONS OPS"] == 20
    assert al["gmbh"]["ING"] == 60
    assert al["gmbh"]["DIGITAL SOLUTIONS"] == 120
    assert al["gmbh"]["TOTAL"] == 200
    # Back Office (300): BO positivo, repartido por % de ingreso
    assert al["back_office"]["BO"] == 300
    assert al["back_office"]["DIGITAL SOLUTIONS"] == 180
    assert al["back_office"]["TOTAL"] == 300

    oa = plan["totales"]["OPERATING_AFTER_ALLOCATION"]
    assert oa["BO"] == 0
    assert oa["ING"] == 150
    # After TOTAL = operating before (700) - GMBH (200): el GMBH reduce el total
    assert oa["TOTAL"] == 500
    assert plan["totales"]["NET_PROFIT"]["BO"] == 0
    assert plan["totales"]["NET_PROFIT"]["TOTAL"] == 500
