import pytest

from core.db import get_connection, init_db
from core.lock import LockHeldError, acquire_lock, get_lock_holder, release_lock


@pytest.fixture
def conn(tmp_path):
    c = get_connection(str(tmp_path / "test.db"))
    init_db(c)
    return c


def test_acquire_lock_when_free(conn):
    acquire_lock(conn, "summary", "2026_May", token="tok-1", locked_by="luis")
    assert get_lock_holder(conn, "summary", "2026_May") == "luis"


def test_acquire_lock_when_taken_raises(conn):
    acquire_lock(conn, "summary", "2026_May", token="tok-1", locked_by="luis")

    with pytest.raises(LockHeldError) as exc_info:
        acquire_lock(conn, "summary", "2026_May", token="tok-2", locked_by="oswaldo")

    assert exc_info.value.locked_by == "luis"


def test_release_lock_frees_it(conn):
    acquire_lock(conn, "summary", "2026_May", token="tok-1", locked_by="luis")
    release_lock(conn, "summary", "2026_May")
    assert get_lock_holder(conn, "summary", "2026_May") is None

    acquire_lock(conn, "summary", "2026_May", token="tok-2", locked_by="oswaldo")
    assert get_lock_holder(conn, "summary", "2026_May") == "oswaldo"
