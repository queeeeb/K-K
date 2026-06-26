import sqlite3
from datetime import datetime, timezone


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pipeline TEXT NOT NULL,
            mes TEXT NOT NULL,
            fila TEXT NOT NULL,
            usuario TEXT,
            valor_anterior TEXT,
            valor_nuevo TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def log_write(
    conn: sqlite3.Connection,
    pipeline: str,
    mes: str,
    fila: str,
    valor_anterior: str | None,
    valor_nuevo: str,
    usuario: str | None = None,
) -> None:
    _ensure_table(conn)
    conn.execute(
        "INSERT INTO audit_log (pipeline, mes, fila, usuario, valor_anterior, valor_nuevo, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (pipeline, mes, fila, usuario, valor_anterior, valor_nuevo, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()


def get_log(conn: sqlite3.Connection, pipeline: str, mes: str) -> list[dict]:
    _ensure_table(conn)
    rows = conn.execute(
        "SELECT fila, usuario, valor_anterior, valor_nuevo, created_at FROM audit_log "
        "WHERE pipeline = ? AND mes = ? ORDER BY id ASC",
        (pipeline, mes),
    ).fetchall()
    return [dict(row) for row in rows]
