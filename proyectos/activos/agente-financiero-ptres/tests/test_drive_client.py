from unittest.mock import MagicMock

import pytest

from core.drive_client import FileNotFoundOnDrive, download_file, find_file_id, upload_file


def test_find_file_id_matches_exact_name():
    service = MagicMock()
    service.files().list().execute.return_value = {
        "files": [{"id": "abc123", "name": "2026_Summary_provision.xlsm"}]
    }

    file_id = find_file_id(service, "2026_Summary_provision.xlsm", folder_id="folder-1")

    assert file_id == "abc123"


def test_find_file_id_raises_when_missing():
    service = MagicMock()
    service.files().list().execute.return_value = {"files": []}

    with pytest.raises(FileNotFoundOnDrive) as exc_info:
        find_file_id(service, "no_existe.xlsx", folder_id="folder-1")

    assert exc_info.value.pattern == "no_existe.xlsx"


def test_download_file_returns_bytes():
    service = MagicMock()
    service.files().get_media().execute.return_value = b"contenido-binario"

    content = download_file(service, "abc123")

    assert content == b"contenido-binario"


def test_upload_file_calls_update():
    service = MagicMock()

    upload_file(service, "abc123", b"contenido-nuevo")

    service.files().update.assert_called()
