import dataclasses
import os
import uvicorn

from core.registry import register
from pipelines.summary.spec import build_summary_spec
from pipelines.pl.spec import build_pl_spec


def _mock_interpret_summary(raw_files):
    return {
        "provisiones_mes_anterior": [
            {"proyecto": "26gmx3000.001", "monto_mxn": 150000, "cc": 3000, "cliente": "BorgWarner MX"},
            {"proyecto": "26gmx4000.002", "monto_mxn": 80000,  "cc": 4000, "cliente": "P3 USA"},
        ],
        "facturas_mes": [
            {"proyecto": "26gmx3000.001-BorgWarner MX- Proyecto Uno", "estado": "Pagado"}
        ],
        "provisiones_nuevas": [
            {"proyecto": "26gmx2000.005", "monto_mxn": 200000, "cc": 2000, "cliente": "Cliente Nuevo"}
        ],
        "alertas": [],
    }


def _mock_interpret_pl(raw_files):
    return {
        "cuentas": [
            {"numero": "4110-002-001-000", "label": "Ventas internacionales", "rubro": "INCOMES",
             "segmentos": {"BO": {"cargos": 0, "abonos": 280000}, "CONS OPS": {"cargos": 0, "abonos": 150000}, "ING": {"cargos": 0, "abonos": 0}, "DIGITAL SOLUTIONS": {"cargos": 0, "abonos": 0}}},
            {"numero": "6100-001-001-000", "label": "Honorarios consultores", "rubro": "EXPENSES",
             "segmentos": {"BO": {"cargos": 90000, "abonos": 0}, "CONS OPS": {"cargos": 60000, "abonos": 0}, "ING": {"cargos": 0, "abonos": 0}, "DIGITAL SOLUTIONS": {"cargos": 0, "abonos": 0}}},
        ]
    }


_summary_spec = build_summary_spec(
    interpret_override=_mock_interpret_summary,
    ruta_origen="agente.db",
    ruta_destino="agente.db",
    hoja_mes_anterior="2026_Abr",
    hoja_mes_nuevo="2026_May",
)
register(dataclasses.replace(
    _summary_spec,
    write=lambda detalle, archivo_destino: {
        "archivo": "mock_summary_mayo.xlsm",
        "filas_escritas": detalle["counts"]["activas"] + detalle["counts"]["nuevas"],
        "canceladas": detalle["counts"]["canceladas"],
        "activas": detalle["counts"]["activas"],
        "nuevas": detalle["counts"]["nuevas"],
    },
))

_pl_spec = build_pl_spec(
    interpret_override=_mock_interpret_pl,
    ruta_destino="agente.db",
    periodo="2026-05",
)
register(dataclasses.replace(
    _pl_spec,
    write=lambda detalle, archivo_destino: {
        "archivo": "mock_pl_mayo.xlsx",
        "net_profit": detalle["plan"]["totales"]["NET_PROFIT"]["TOTAL"],
    },
))


if __name__ == "__main__":
    host = os.getenv("AGENTE_HOST", "127.0.0.1")
    uvicorn.run("core.api:app", host=host, port=8000, reload=False)
