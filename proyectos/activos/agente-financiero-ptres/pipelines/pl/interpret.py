"""Interpretación con IA del export de Contpaqi. Única pieza que llama a Claude.
Devuelve SOLO estructura y clasificación (nunca montos calculados): la máquina de
estados de tipos de fila, el mapa de columnas y la clasificación cuenta->grupo->rubro
con su label en inglés. Ver pipelines/pl/ESPECIFICACION.md §3.1, §3.2, §3.5 y §4.
"""
import json


def _ask_claude_for_structure(anthropic_client, prompt: str) -> dict:
    message = anthropic_client.messages.create(
        model="claude-opus-4-8",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(message.content[0].text)


def interpret_estructura(rows: list[list], anthropic_client) -> dict:
    prompt = (
        "Este es un export de Contpaqi 'Movimientos Auxiliares por Segmento de Negocio'. "
        "Es un reporte jerárquico, no una tabla plana. Hay 4 tipos de fila: "
        "(A) CUENTA: la columna A tiene un número de cuenta contable (formato NNNN-...); su nombre está en la columna B. "
        "(B) SEGMENTO: la columna A empieza con 'Segmento:'. "
        "(C) TOTAL DE SEGMENTO: la columna E empieza con 'Total Seg.'; los cargos están en la columna F y los abonos en la columna G. "
        "(D) MOVIMIENTO DETALLE (Diario): dentro de Ventas Nacionales, la columna B = 'Diario' y el cliente está en la columna D. "
        "Identifica el periodo (suele estar en A3 o A2) y, por número de fila, qué filas son CUENTA, SEGMENTO, TOTAL_SEGMENTO y DIARIO. "
        "Responde solo JSON con las llaves: periodo, columnas, filas_cuenta, filas_segmento, filas_total_segmento, filas_diario.\n\n"
        f"Filas: {rows}"
    )
    return _ask_claude_for_structure(anthropic_client, prompt)


def clasificar_cuentas(cuentas: list[dict], anthropic_client) -> dict:
    prompt = (
        "Clasifica cada cuenta contable a su rubro del Estado de Resultados (P&L) de P-TRES GROUP. "
        "Rubros posibles: INCOMES (ventas, prefijo 4110), OTHER_INCOMES (4210/4310/4510), "
        "EXPENSES (gastos 6100-001 a 6100-008), OTHER_EXPENSES (6100-009), ACCRUED_TAXES (8000 o 0000-000-80). "
        "Analiza TODAS las cuentas por su número Y su nombre, no solo las que ya conoces: si aparece una cuenta o "
        "cliente nuevo, clasifícalo a su rubro correcto y márcalo con nuevo=true (NO lo mandes a un cajón genérico). "
        "Traduce el nombre al label en inglés del P&L (ES->EN). "
        "Responde solo JSON con la llave 'cuentas': lista de objetos con numero, grupo, rubro, label_en, nuevo.\n\n"
        f"Cuentas: {cuentas}"
    )
    return _ask_claude_for_structure(anthropic_client, prompt)


def normalizar_cliente(nombre: str, anthropic_client) -> dict:
    prompt = (
        "Normaliza la razón social de un cliente de ventas nacionales a su nombre canónico del P&L. "
        "Distintas variantes de la misma empresa (con/sin S.A. de C.V., con/sin sufijos) deben mapear al mismo "
        "nombre canónico. Responde solo JSON con la llave: canonico.\n\n"
        f"Cliente: {nombre}"
    )
    return _ask_claude_for_structure(anthropic_client, prompt)
