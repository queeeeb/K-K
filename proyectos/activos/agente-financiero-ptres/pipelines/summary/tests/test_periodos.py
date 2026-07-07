from datetime import datetime

from pipelines.summary.periodos import normalizar_periodo


def test_normaliza_datetime_al_mes_del_periodo():
    assert normalizar_periodo(datetime(2026, 4, 30)) == (2026, "Abril")


def test_normaliza_nombre_mes_espanol_con_anio_contexto():
    assert normalizar_periodo("Abril", anio_contexto=2026) == (2026, "Abril")


def test_normaliza_nombre_mes_con_espacios_y_mayusculas():
    assert normalizar_periodo("  MAYO ", anio_contexto=2026) == (2026, "Mayo")


def test_normaliza_abreviatura_con_anio_de_dos_digitos():
    assert normalizar_periodo("ENE26") == (2026, "Enero")
    assert normalizar_periodo("feb26") == (2026, "Febrero")
    assert normalizar_periodo("DIC25") == (2025, "Diciembre")


def test_normaliza_abreviatura_sin_anio_usa_contexto():
    assert normalizar_periodo("ago", anio_contexto=2026) == (2026, "Agosto")


def test_devuelve_none_si_no_reconoce():
    assert normalizar_periodo("se facturó junto", anio_contexto=2026) is None
    assert normalizar_periodo(None) is None
