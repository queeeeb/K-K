import io

from googleapiclient.http import MediaIoBaseUpload


class FileNotFoundOnDrive(Exception):
    def __init__(self, pattern: str):
        self.pattern = pattern
        super().__init__(f"No file matching '{pattern}' found on Drive")


def find_file_id(service, name_pattern: str, folder_id: str) -> str:
    response = (
        service.files()
        .list(q=f"'{folder_id}' in parents and name = '{name_pattern}'", fields="files(id, name)")
        .execute()
    )
    files = response.get("files", [])
    if not files:
        raise FileNotFoundOnDrive(name_pattern)
    return files[0]["id"]


def download_file(service, file_id: str) -> bytes:
    return service.files().get_media(fileId=file_id).execute()


def upload_file(service, file_id: str, content: bytes) -> None:
    media = MediaIoBaseUpload(io.BytesIO(content), mimetype="application/octet-stream")
    service.files().update(fileId=file_id, media_body=media).execute()
