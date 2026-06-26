from core.pipeline_spec import PipelineSpec
from pipelines.summary.calculate import reconciliar
from pipelines.summary.write import escribir_hoja_mes

SOURCES = [
    "{mes}_Facturacion_sem.xlsx",
    "FORMATO_PROVISIONES_P3_DS_{mes}.xlsx",
    "Provisiones_ES_{mes}.xlsx",
    "PROVISIONES_Overview_Projects_{mes}.xlsx",
]


def build_summary_spec(
    interpret_override,
    ruta_origen: str,
    ruta_destino: str,
    hoja_mes_anterior: str,
    hoja_mes_nuevo: str,
) -> PipelineSpec:
    def calculate(estructura: dict, estado_anterior) -> dict:
        resultado = reconciliar(
            provisiones_mes_anterior=estructura["provisiones_mes_anterior"],
            facturas_mes=estructura["facturas_mes"],
            provisiones_nuevas=estructura["provisiones_nuevas"],
            alertas=estructura.get("alertas", []),
        )
        filas = [
            [
                "", "Provision", 2026, hoja_mes_nuevo.split("_")[1], p["cc"], p["cliente"], "",
                p["proyecto"], "MXN", p["monto_mxn"], 1, p["monto_mxn"], 0, p["monto_mxn"], 0, 0,
                p["monto_mxn"], "", "",
            ]
            for p in resultado["activas"] + resultado["nuevas"]
        ]
        counts = {
            "canceladas": len(resultado["canceladas"]),
            "activas": len(resultado["activas"]),
            "nuevas": len(resultado["nuevas"]),
        }
        return {"resumen": resultado, "detalle": {"filas": filas, "counts": counts}}

    def write(detalle: dict, archivo_destino) -> dict:
        escribir_hoja_mes(
            ruta_origen=ruta_origen,
            ruta_destino=ruta_destino,
            hoja_mes_anterior=hoja_mes_anterior,
            hoja_mes_nuevo=hoja_mes_nuevo,
            filas=detalle["filas"],
        )
        counts = detalle["counts"]
        return {
            "archivo": ruta_destino,
            "filas_escritas": counts["activas"] + counts["nuevas"],
            "canceladas": counts["canceladas"],
            "activas": counts["activas"],
            "nuevas": counts["nuevas"],
        }

    return PipelineSpec(
        name="summary",
        sources=SOURCES,
        interpret=interpret_override,
        calculate=calculate,
        write=write,
    )
