import sqlite3

from core.db import get_connection, init_db


def test_init_db_creates_tables(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = get_connection(db_path)
    init_db(conn)

    tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert {"plans", "locks"}.issubset(tables)


def test_get_connection_returns_row_factory_dict(tmp_path):
    db_path = str(tmp_path / "test.db")
    conn = get_connection(db_path)
    init_db(conn)
    conn.execute(
        "INSERT INTO plans (token, pipeline, mes, plan_json, created_at) VALUES (?, ?, ?, ?, ?)",
        ("tok-1", "summary", "2026_May", "{}", "2026-06-24T00:00:00"),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM plans WHERE token = ?", ("tok-1",)).fetchone()
    assert row["pipeline"] == "summary"


def test_init_db_creates_usuarios_table():
    conn = get_connection(":memory:")
    init_db(conn)

    conn.execute(
        "INSERT INTO usuarios (username, password_hash, created_at) VALUES (?, ?, datetime('now'))",
        ("luis", "hash-falso"),
    )
    conn.commit()

    row = conn.execute("SELECT username FROM usuarios WHERE username = ?", ("luis",)).fetchone()
    assert row["username"] == "luis"


def test_usuarios_username_is_unique():
    conn = get_connection(":memory:")
    init_db(conn)

    conn.execute(
        "INSERT INTO usuarios (username, password_hash, created_at) VALUES (?, ?, datetime('now'))",
        ("luis", "hash-falso"),
    )
    conn.commit()

    try:
        conn.execute(
            "INSERT INTO usuarios (username, password_hash, created_at) VALUES (?, ?, datetime('now'))",
            ("luis", "otro-hash"),
        )
        conn.commit()
        raised = False
    except sqlite3.IntegrityError:
        raised = True

    assert raised
