from core.pipeline_spec import PipelineSpec
from pipelines.summary.calculate import actualizar_nombres_nuevas, reconciliar
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
        hoja_mes_nuevo_actual = estructura.get("hoja_mes_nuevo") or hoja_mes_nuevo
        hoja_mes_anterior_actual = estructura.get("hoja_mes_anterior") or hoja_mes_anterior
        ruta_origen_actual = estructura.get("ruta_base") or ruta_origen

        resultado = reconciliar(
            provisiones_mes_anterior=estructura["provisiones_mes_anterior"],
            facturas_mes=estructura["facturas_mes"],
            provisiones_actuales=estructura["provisiones_actuales"],
            alertas=estructura.get("alertas", []),
            codigos_conocidos=estructura.get("codigos_conocidos"),
        )
        anio_actual, periodo_actual = hoja_mes_nuevo_actual.split("_", 1)

        def _fila(p: dict, cierre: str) -> list:
            moneda = p.get("moneda", "MXN")
            monto_original = p.get("monto_original", p["monto_mxn"])
            tc = p.get("tc", 1)
            anio = p.get("anio") or int(anio_actual)
            periodo = p.get("periodo") or periodo_actual
            cancelada = cierre == "Cancelar"
            usd = monto_original if cancelada and moneda == "USD" else ""
            mxn = p["monto_mxn"] if cancelada and moneda == "MXN" else ""
            eur = monto_original if cancelada and moneda == "EUR" else ""
            cad = monto_original if cancelada and moneda == "CAD" else ""
            total_mxn = p["monto_mxn"] if cancelada else ""
            return [
                "", cierre, anio, periodo, p["cc"], p["cliente"], p.get("nombre_proyecto", ""),
                p["proyecto"], moneda, monto_original, tc, p["monto_mxn"], usd, mxn, eur, cad,
                total_mxn, "", "",
            ]

        filas = (
            [_fila(p, "Provision") for p in resultado["activas"] + resultado["nuevas"]]
            + [_fila(p, "Cancelar") for p in resultado["canceladas"]]
        )
        counts = {
            "canceladas": len(resultado["canceladas"]),
            "activas": len(resultado["activas"]),
            "nuevas": len(resultado["nuevas"]),
        }
        detalle = {
            "filas": filas,
            "counts": counts,
            "ruta_origen": ruta_origen_actual,
            "hoja_mes_anterior": hoja_mes_anterior_actual,
            "hoja_mes_nuevo": hoja_mes_nuevo_actual,
        }
        return {"resumen": resultado, "detalle": detalle}

    def write(detalle: dict, archivo_destino) -> dict:
        destino = archivo_destino or ruta_destino
        escribir_hoja_mes(
            ruta_origen=detalle["ruta_origen"],
            ruta_destino=destino,
            hoja_mes_anterior=detalle["hoja_mes_anterior"],
            hoja_mes_nuevo=detalle["hoja_mes_nuevo"],
            filas=detalle["filas"],
        )
        counts = detalle["counts"]
        return {
            "archivo": destino,
            "filas_escritas": counts["activas"] + counts["nuevas"] + counts["canceladas"],
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
        nombrar=actualizar_nombres_nuevas,
    )
