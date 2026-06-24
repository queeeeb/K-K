import sqlite3
from datetime import datetime, timezone


class LockHeldError(Exception):
    def __init__(self, locked_by: str):
        self.locked_by = locked_by
        super().__init__(f"Locked by {locked_by}")


def get_lock_holder(conn: sqlite3.Connection, pipeline: str, mes: str) -> str | None:
    row = conn.execute(
        "SELECT locked_by FROM locks WHERE pipeline = ? AND mes = ?", (pipeline, mes)
    ).fetchone()
    return row["locked_by"] if row else None


def acquire_lock(
    conn: sqlite3.Connection, pipeline: str, mes: str, token: str, locked_by: str
) -> None:
    holder = get_lock_holder(conn, pipeline, mes)
    if holder is not None:
        raise LockHeldError(holder)

    conn.execute(
        "INSERT INTO locks (pipeline, mes, token, locked_by, created_at) VALUES (?, ?, ?, ?, ?)",
        (pipeline, mes, token, locked_by, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()


def release_lock(conn: sqlite3.Connection, pipeline: str, mes: str) -> None:
    conn.execute("DELETE FROM locks WHERE pipeline = ? AND mes = ?", (pipeline, mes))
    conn.commit()
