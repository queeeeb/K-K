import pytest

from core.audit_log import get_log, log_write
from core.db import get_connection, init_db


@pytest.fixture
def conn(tmp_path):
    c = get_connection(str(tmp_path / "test.db"))
    init_db(c)
    return c


def test_log_write_and_get_log(conn):
    log_write(conn, "summary", "2026_May", fila="26gmx3000.104", valor_anterior="1000.00", valor_nuevo="1200.00", usuario="luis")
    log_write(conn, "summary", "2026_May", fila="26gmx2000.007", valor_anterior=None, valor_nuevo="500.00")

    entries = get_log(conn, "summary", "2026_May")

    assert len(entries) == 2
    assert entries[0]["fila"] == "26gmx3000.104"
    assert entries[0]["usuario"] == "luis"
    assert entries[0]["valor_anterior"] == "1000.00"
    assert entries[1]["valor_anterior"] is None
    assert entries[1]["usuario"] is None
