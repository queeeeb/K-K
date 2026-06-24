import json
import os
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core import audit_log, registry
from core.db import get_connection, init_db
from core.lock import LockHeldError, acquire_lock, release_lock


class ProcesarRequest(BaseModel):
    mes: str
    usuario: str


class TokenRequest(BaseModel):
    token: str


app = FastAPI(title="Agente Financiero P3")


def _db_path() -> str:
    return os.environ.get("AGENTE_DB_PATH", "agente.db")


def _conn():
    conn = get_connection(_db_path())
    init_db(conn)
    return conn


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/procesar/{pipeline}")
def procesar(pipeline: str, body: ProcesarRequest):
    spec = registry.get(pipeline)
    conn = _conn()
    token = str(uuid.uuid4())

    try:
        acquire_lock(conn, pipeline, body.mes, token=token, locked_by=body.usuario)
    except LockHeldError as exc:
        raise HTTPException(status_code=409, detail=f"Locked by {exc.locked_by}")

    raw_files = {source: None for source in spec.sources}
    estructura = spec.interpret(raw_files)
    plan = spec.calculate(estructura, estado_anterior=None)

    conn.execute(
        "INSERT INTO plans (token, pipeline, mes, plan_json, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
        (token, pipeline, body.mes, json.dumps(plan)),
    )
    conn.commit()

    return {"token": token, "resumen": plan["resumen"]}


@app.post("/confirmar/{pipeline}")
def confirmar(pipeline: str, body: TokenRequest):
    spec = registry.get(pipeline)
    conn = _conn()

    row = conn.execute(
        "SELECT mes, plan_json FROM plans WHERE token = ? AND pipeline = ?", (body.token, pipeline)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Token not found")

    plan = json.loads(row["plan_json"])
    reporte = spec.write(plan["detalle"], archivo_destino=None)

    audit_log.log_write(
        conn, pipeline, row["mes"], fila="*", valor_anterior=None, valor_nuevo=json.dumps(reporte)
    )
    release_lock(conn, pipeline, row["mes"])
    conn.execute("DELETE FROM plans WHERE token = ?", (body.token,))
    conn.commit()

    return {"reporte": reporte}


@app.post("/rechazar/{pipeline}")
def rechazar(pipeline: str, body: TokenRequest):
    conn = _conn()
    row = conn.execute(
        "SELECT mes FROM plans WHERE token = ? AND pipeline = ?", (body.token, pipeline)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Token not found")

    release_lock(conn, pipeline, row["mes"])
    conn.execute("DELETE FROM plans WHERE token = ?", (body.token,))
    conn.commit()

    return {"status": "rechazado"}
