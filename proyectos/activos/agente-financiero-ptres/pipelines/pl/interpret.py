import io
import json

import openpyxl

from pipelines.pl.extract import extraer_cuentas


def _ask_claude(anthropic_client, prompt: str, max_tokens: int = 4096) -> dict:
    message = anthropic_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    text = message.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)


_BATCH_SIZE = 30


def _clasificar_batch(cuentas: list[dict], anthropic_client) -> list[dict]:
    prompt = (
        "Clasifica cada cuenta contable a su rubro del Estado de Resultados (P&L) de P-TRES GROUP. "
        "Rubros posibles: INCOMES (ventas, prefijo 4110), OTHER_INCOMES (4210/4310/4510), "
        "EXPENSES (gastos 6100-001 a 6100-008), OTHER_EXPENSES (6100-009), ACCRUED_TAXES (8000 o 0000-000-80). "
        "Si aparece una cuenta nueva, clasifícala a su rubro correcto y márcala con nuevo=true. "
        "Cuentas sin rubro P&L (capital, balance, etc.) deben tener rubro null. "
        "Traduce el nombre al label en inglés del P&L (ES->EN). "
        "Responde SOLO JSON sin markdown: {\"cuentas\": [{numero, rubro, label_en, nuevo}]}.\n\n"
        f"Cuentas: {cuentas}"
    )
    return _ask_claude(anthropic_client, prompt, max_tokens=4096).get("cuentas", [])


def clasificar_cuentas(cuentas: list[dict], anthropic_client) -> dict:
    resultados = []
    for i in range(0, len(cuentas), _BATCH_SIZE):
        resultados.extend(_clasificar_batch(cuentas[i:i + _BATCH_SIZE], anthropic_client))
    return {"cuentas": resultados}


def interpret_pl(wb_bytes: bytes, anthropic_client) -> dict:
    wb = openpyxl.load_workbook(io.BytesIO(wb_bytes), data_only=True)
    ws = wb.active

    cuentas_raw = extraer_cuentas(ws)

    relevantes = [
        c for c in cuentas_raw
        if c["numero"].strip()[0] in ("4", "6", "8") and c["segmentos"]
    ]

    cuentas_input = [{"numero": c["numero"], "nombre": c["nombre"]} for c in relevantes]
    clasificacion = clasificar_cuentas(cuentas_input, anthropic_client)
    clf_map = {c["numero"]: c for c in clasificacion.get("cuentas", [])}

    cuentas_final = []
    for cuenta in relevantes:
        clf = clf_map.get(cuenta["numero"])
        if clf and clf.get("rubro"):
            cuentas_final.append({
                "numero": cuenta["numero"],
                "label": clf.get("label_en", cuenta["nombre"]),
                "rubro": clf["rubro"],
                "segmentos": cuenta["segmentos"],
            })

    return {"cuentas": cuentas_final}
