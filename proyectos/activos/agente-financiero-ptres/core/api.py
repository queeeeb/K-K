import json
import os
import re
import uuid

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from typing import Optional

from core import audit_log, auth, registry, uploads
from core.db import get_connection, init_db
from core.lock import LockHeldError, acquire_lock, release_lock


class ProcesarRequest(BaseModel):
    mes: str


class TokenRequest(BaseModel):
    token: str


class NombrarRequest(BaseModel):
    token: str
    nombres: dict[str, str]


class LoginRequest(BaseModel):
    usuario: str
    password: str


limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Agente Financiero P3", docs_url=None, redoc_url=None)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
_bearer_scheme = HTTPBearer()


def _db_path() -> str:
    return os.environ.get("AGENTE_DB_PATH", "agente.db")


def _conn():
    conn = get_connection(_db_path())
    init_db(conn)
    return conn


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme)) -> str:
    try:
        return auth.decode_access_token(credentials.credentials)
    except auth.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")


def _audit_entries_from_plan(pipeline: str, plan: dict) -> list[dict]:
    entries = []
    if pipeline == "summary":
        resumen = plan.get("resumen", {})
        for r in resumen.get("cerradas", []):
            entries.append({"fila": r["proyecto"], "anterior": str(r["monto_mxn"]), "nuevo": "Cancelar"})
        for r in resumen.get("nuevas", []):
            entries.append({"fila": r["proyecto"], "anterior": None, "nuevo": str(r["monto_mxn"])})
    elif pipeline == "pl":
        rubros = plan.get("detalle", {}).get("plan", {}).get("rubros", {})
        for cuentas in rubros.values():
            for c in cuentas:
                entries.append({"fila": c.get("label", c["numero"]), "anterior": None, "nuevo": str(round(c["montos"]["TOTAL"], 2))})
    if not entries:
        entries.append({"fila": "*", "anterior": None, "nuevo": "confirmado"})
    return entries


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


_MEDIA_TYPES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xlsm": "application/vnd.ms-excel.sheet.macroEnabled.12",
}


@app.get("/descargar/{archivo}")
def descargar(archivo: str, usuario_autenticado: str = Depends(get_current_user)):
    import re
    from fastapi.responses import FileResponse
    match = re.fullmatch(r"[A-Za-z0-9_\-\.]+\.(xlsx|xlsm)", archivo)
    if not match:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")
    reportes_dir = os.environ.get("AGENTE_REPORTES_DIR", "reportes")
    ruta = os.path.join(reportes_dir, archivo)
    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return FileResponse(ruta, filename=archivo, media_type=_MEDIA_TYPES[match.group(1)])


@app.post("/login")
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest):
    conn = _conn()
    try:
        token = auth.autenticar(conn, body.usuario, body.password)
    except auth.InvalidCredentialsError:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    return {"access_token": token, "token_type": "bearer", "expires_in": auth.TOKEN_EXPIRE_HOURS * 3600}


def _validar_pipeline(pipeline: str) -> str:
    if not re.fullmatch(r"[a-z0-9_-]+", pipeline):
        raise HTTPException(status_code=400, detail="Pipeline inválido")
    try:
        return registry.get(pipeline)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Pipeline '{pipeline}' no registrado")


@app.post("/procesar/{pipeline}")
async def procesar(pipeline: str, request: Request, usuario_autenticado: str = Depends(get_current_user)):
    spec = _validar_pipeline(pipeline)

    form = await request.form()
    mes = form.get("mes")
    if not mes:
        raise HTTPException(status_code=400, detail="Falta el campo 'mes'")

    tc = {}
    for moneda, campo in (("USD", "tc_usd"), ("EUR", "tc_eur"), ("CAD", "tc_cad")):
        valor = form.get(campo)
        if valor:
            try:
                tc[moneda] = float(valor)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Tipo de cambio inválido en {campo}")

    subidas = {k: v for k, v in form.items() if hasattr(v, "filename")}
    nombres = {slot: f.filename for slot, f in subidas.items()}
    try:
        uploads.validar_subidas(pipeline, nombres)
    except uploads.SubidaInvalida as exc:
        raise HTTPException(status_code=400, detail=exc.detalle)

    token = str(uuid.uuid4())
    archivos_bytes = {slot: (f.filename, await f.read()) for slot, f in subidas.items()}
    for f in subidas.values():
        await f.close()
    rutas = uploads.guardar_archivos(token, archivos_bytes) if archivos_bytes else {}

    conn = _conn()
    try:
        acquire_lock(conn, pipeline, mes, token=token, locked_by=usuario_autenticado)
    except LockHeldError as exc:
        uploads.limpiar_token(token)
        raise HTTPException(status_code=409, detail=f"Locked by {exc.locked_by}")

    try:
        # raw_files = {slot: ruta del archivo subido} + '_mes' (mes objetivo del proceso).
        # El interpret de cada pipeline lee de ahí; los que no necesitan '_mes' lo ignoran.
        estructura = spec.interpret({**rutas, "_mes": mes, "_tc": tc})
        plan = spec.calculate(estructura, estado_anterior=None)

        conn.execute(
            "INSERT INTO plans (token, pipeline, mes, plan_json, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
            (token, pipeline, mes, json.dumps(plan)),
        )
        conn.commit()
    except Exception:
        release_lock(conn, pipeline, mes)
        uploads.limpiar_token(token)
        raise

    return {"token": token, "resumen": plan["resumen"]}


@app.post("/nombrar/{pipeline}")
def nombrar(pipeline: str, body: NombrarRequest, usuario_autenticado: str = Depends(get_current_user)):
    spec = _validar_pipeline(pipeline)
    if spec.nombrar is None:
        raise HTTPException(status_code=400, detail=f"Pipeline '{pipeline}' no soporta nombrar")

    conn = _conn()
    row = conn.execute(
        "SELECT plan_json FROM plans WHERE token = ? AND pipeline = ?", (body.token, pipeline)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Token not found")

    plan = spec.nombrar(json.loads(row["plan_json"]), body.nombres)
    conn.execute("UPDATE plans SET plan_json = ? WHERE token = ?", (json.dumps(plan), body.token))
    conn.commit()

    return {"resumen": plan["resumen"]}


@app.post("/confirmar/{pipeline}")
def confirmar(pipeline: str, body: TokenRequest, usuario_autenticado: str = Depends(get_current_user)):
    spec = _validar_pipeline(pipeline)
    conn = _conn()

    row = conn.execute(
        "SELECT mes, plan_json FROM plans WHERE token = ? AND pipeline = ?", (body.token, pipeline)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Token not found")

    plan = json.loads(row["plan_json"])
    try:
        reporte = spec.write(plan["detalle"], archivo_destino=None)
    except Exception:
        release_lock(conn, pipeline, row["mes"])
        conn.execute("DELETE FROM plans WHERE token = ?", (body.token,))
        conn.commit()
        raise

    for entry in _audit_entries_from_plan(pipeline, plan):
        audit_log.log_write(
            conn, pipeline, row["mes"],
            fila=entry["fila"], valor_anterior=entry["anterior"],
            valor_nuevo=entry["nuevo"], usuario=usuario_autenticado,
        )
    release_lock(conn, pipeline, row["mes"])
    conn.execute("DELETE FROM plans WHERE token = ?", (body.token,))
    conn.commit()
    uploads.limpiar_token(body.token)

    return {"reporte": reporte}


@app.get("/pendientes")
def pendientes(usuario_autenticado: str = Depends(get_current_user)):
    conn = _conn()
    rows = conn.execute(
        "SELECT l.pipeline, l.mes, p.token, p.plan_json "
        "FROM locks l JOIN plans p ON l.pipeline = p.pipeline AND l.mes = p.mes "
        "WHERE l.locked_by = ?",
        (usuario_autenticado,),
    ).fetchall()
    result = []
    for row in rows:
        plan = json.loads(row["plan_json"])
        result.append({
            "pipeline": row["pipeline"],
            "mes": row["mes"],
            "token": row["token"],
            "resumen": plan["resumen"],
        })
    return result


@app.get("/recuperar/{pipeline}")
def recuperar(pipeline: str, mes: str, usuario_autenticado: str = Depends(get_current_user)):
    _validar_pipeline(pipeline)
    conn = _conn()
    holder = get_lock_holder(conn, pipeline, mes)
    if holder != usuario_autenticado:
        raise HTTPException(status_code=404, detail="No hay proceso activo tuyo para este pipeline/mes")
    row = conn.execute(
        "SELECT token, plan_json FROM plans WHERE pipeline = ? AND mes = ?", (pipeline, mes)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    plan = json.loads(row["plan_json"])
    return {"token": row["token"], "resumen": plan["resumen"]}


@app.get("/bitacora")
def bitacora(pipeline: Optional[str] = None, usuario_autenticado: str = Depends(get_current_user)):
    conn = _conn()
    return audit_log.get_all(conn, pipeline)


@app.post("/rechazar/{pipeline}")
def rechazar(pipeline: str, body: TokenRequest, usuario_autenticado: str = Depends(get_current_user)):
    _validar_pipeline(pipeline)
    conn = _conn()
    row = conn.execute(
        "SELECT mes FROM plans WHERE token = ? AND pipeline = ?", (body.token, pipeline)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Token not found")

    audit_log.log_write(
        conn, pipeline, row["mes"], fila="*", valor_anterior=None,
        valor_nuevo="rechazado", usuario=usuario_autenticado,
    )
    release_lock(conn, pipeline, row["mes"])
    conn.execute("DELETE FROM plans WHERE token = ?", (body.token,))
    conn.commit()

    return {"status": "rechazado"}
