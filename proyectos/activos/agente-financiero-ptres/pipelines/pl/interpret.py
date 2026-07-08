"""Interpretación del export de Contpaqi -> estructura clasificada.

La clasificación cuenta->grupo->rubro y la traducción ES->EN son deterministas
(portadas del macro GenerarPL.bas, ver referencia.py). La IA queda disponible solo
para normalizar razones sociales de clientes de Ventas Nacionales y marcar cuentas
nuevas; el cálculo de montos nunca pasa por la IA (ESPECIFICACION §4).
"""
import io

import openpyxl

from pipelines.pl.extract import CUENTA_VENTAS_NACIONALES, extraer
from pipelines.pl.referencia import (
    GRUPO_VENTAS_NACIONALES,
    LABEL_PTU,
    clasificar_por_numero,
    normalizar_cliente,
    traducir,
)


def clasificar_estructura(cuentas: list[dict], ventas_nacionales: list[dict]) -> dict:
    """Recibe cuentas crudas + desglose de ventas nacionales y devuelve las cuentas
    clasificadas listas para calcular. Determinista.
    """
    clasificadas = []
    for cuenta in cuentas:
        numero = cuenta["numero"]
        if numero == CUENTA_VENTAS_NACIONALES:
            continue  # lump-sum: se reemplaza por el desglose por cliente
        if not cuenta.get("segmentos"):
            continue
        grupo, rubro = clasificar_por_numero(numero)
        if not rubro:
            continue  # cuenta ajena al P&L: se ignora
        label = traducir(cuenta["nombre"], grupo)
        if label == LABEL_PTU:
            rubro = "EXPENSES"  # PTU va en Expenses, no en Accrued Taxes (convención vf final)
        clasificadas.append({
            "numero": numero,
            "label": label,
            "rubro": rubro,
            "grupo": grupo,
            "segmentos": cuenta["segmentos"],
        })

    ns_por_cliente: dict[str, dict] = {}
    for mov in ventas_nacionales:
        cliente = normalizar_cliente(mov["cliente"])
        cuenta = ns_por_cliente.setdefault(cliente, {
            "numero": f"4110NS-{cliente}",
            "label": cliente,
            "rubro": "INCOMES",
            "grupo": GRUPO_VENTAS_NACIONALES,
            "segmentos": {},
        })
        seg = cuenta["segmentos"].setdefault(mov["segmento"], {"cargos": 0.0, "abonos": 0.0})
        seg["abonos"] += mov["monto"]

    clasificadas.extend(ns_por_cliente.values())
    return {"cuentas": clasificadas, "alertas": []}


def interpret_pl(wb_bytes: bytes, anthropic_client=None) -> dict:
    wb = openpyxl.load_workbook(io.BytesIO(wb_bytes), data_only=True)
    extraido = extraer(wb.active)
    return clasificar_estructura(extraido["cuentas"], extraido["ventas_nacionales"])
