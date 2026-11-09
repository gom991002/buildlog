from datetime import UTC
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from app.core.config import settings
from app.models.material import FILE_RULES, ORIGINAL_FILENAME_MAX, Material
from app.schemas.material import MaterialResponse

FILE_TYPE_RULE = "PNG·JPG 이미지 또는 MP4 영상만 올릴 수 있습니다."
FILE_SIZE_RULE = "이미지는 5MB, 영상은 30MB까지 올릴 수 있습니다."

# File name extension -> the content type it must really contain.
EXTENSIONS = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".mp4": "video/mp4"}

CHUNK_SIZE = 1024 * 1024


class FileRejected(ValueError):
    """The upload breaks a file rule; the message is shown to the user."""


def clean_filename(name: str | None) -> str:
    """The bare file name for display only: no folders, at most 255 characters."""
    bare = (name or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
    return bare[:ORIGINAL_FILENAME_MAX] or "file"


def detect_content_type(head: bytes) -> str | None:
    """Judge the type from the file's first bytes, not from what the browser claims."""
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head[4:8] == b"ftyp":
        return "video/mp4"
    return None


def check_file(filename: str, head: bytes) -> str:
    """The content type of an allowed file, or FileRejected."""
    claimed = EXTENSIONS.get(Path(filename).suffix.lower())
    actual = detect_content_type(head)
    if claimed is None or actual != claimed:
        raise FileRejected(FILE_TYPE_RULE)
    return actual


def save_upload(source: BinaryIO, content_type: str) -> tuple[str, int]:
    """Copy the upload into the upload folder under a random name; returns (name, size).

    Stops and removes the partial file as soon as the type's size limit is passed.
    """
    extension, limit = FILE_RULES[content_type]
    stored_filename = f"{uuid4().hex}{extension}"
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    path = file_path(stored_filename)
    size = 0
    try:
        with path.open("xb") as target:
            while chunk := source.read(CHUNK_SIZE):
                size += len(chunk)
                if size > limit:
                    raise FileRejected(FILE_SIZE_RULE)
                target.write(chunk)
        if size == 0:
            raise FileRejected("빈 파일은 올릴 수 없습니다.")
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return stored_filename, size


def file_path(stored_filename: str) -> Path:
    return settings.upload_dir / stored_filename


def remove_file(stored_filename: str) -> None:
    file_path(stored_filename).unlink(missing_ok=True)


def to_response(material: Material) -> MaterialResponse:
    created_at = material.created_at
    if created_at.tzinfo is None:
        # SQLite (tests) drops the time zone; every stored time is UTC.
        created_at = created_at.replace(tzinfo=UTC)
    return MaterialResponse(
        id=material.id,
        title=material.title,
        memo=material.memo,
        original_filename=material.original_filename,
        content_type=material.content_type,
        file_size=material.file_size,
        ai_summary=material.ai_summary,
        ai_status=material.ai_status,
        created_at=created_at,
        file_url=f"/api/materials/{material.id}/file",
    )
