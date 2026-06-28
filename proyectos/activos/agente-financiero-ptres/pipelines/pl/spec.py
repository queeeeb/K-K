"""Implementa el contrato PipelineSpec para el pipeline P&L y lo conecta al núcleo.
El `interpret` real (que compone Drive + Claude en un dict de cuentas) se inyecta;
en tests se sustituye por un stub fijo, igual que en el pipeline Summary.
"""
from core.pipeline_spec import PipelineSpec
from pipelines.pl.calculate import COLUMNAS_SALIDA, calcular_pl
from pipelines.pl.write import escribir_pl

SOURCES = ["Movimientos_Auxiliares_Segmento_{mes}.xlsx"]


def build_pl_spec(interpret_override, ruta_destino: str, periodo: str) -> PipelineSpec:
    def calculate(estructura: dict, estado_anterior=None) -> dict:
        plan = calcular_pl(estructura["cuentas"])
        totales = plan["totales"]
        _rubros = ["INCOMES", "EXPENSES", "OPERATING_PROFIT", "OTHER_INCOMES", "OTHER_EXPENSES", "ACCRUED_TAXES", "NET_PROFIT"]
        resumen = {
            "incomes": totales["INCOMES"]["TOTAL"],
            "expenses": totales["EXPENSES"]["TOTAL"],
            "operating_profit": totales["OPERATING_PROFIT"]["TOTAL"],
            "other_incomes": totales["OTHER_INCOMES"]["TOTAL"],
            "other_expenses": totales["OTHER_EXPENSES"]["TOTAL"],
            "accrued_taxes": totales["ACCRUED_TAXES"]["TOTAL"],
            "net_profit": totales["NET_PROFIT"]["TOTAL"],
            "por_segmento": {
                r: {col: totales[r][col] for col in COLUMNAS_SALIDA}
                for r in _rubros
            },
        }
        return {"resumen": resumen, "detalle": {"plan": plan, "periodo": periodo}}

    def write(detalle: dict, archivo_destino=None) -> dict:
        destino = archivo_destino or ruta_destino
        escribir_pl(ruta_destino=destino, plan=detalle["plan"], periodo=detalle["periodo"])
        return {
            "archivo": destino,
            "net_profit": detalle["plan"]["totales"]["NET_PROFIT"]["TOTAL"],
        }

    return PipelineSpec(
        name="pl",
        sources=SOURCES,
        interpret=interpret_override,
        calculate=calculate,
        write=write,
    )
