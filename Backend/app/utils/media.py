from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings


ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def ensure_media_directories() -> None:
    settings.media_root_path.mkdir(parents=True, exist_ok=True)


def _public_media_prefix() -> str:
    return f"{settings.normalized_media_url_path.rstrip('/')}/"


def _relative_from_media_url(media_url: str) -> str | None:
    value = str(media_url or "").strip()
    if not value:
        return None

    prefix = _public_media_prefix()
    if not value.startswith(prefix):
        return None

    relative = value[len(prefix) :].lstrip("/")
    return relative or None


def is_local_media_url(media_url: str | None) -> bool:
    if media_url is None:
        return False
    return _relative_from_media_url(media_url) is not None


def _resolve_storage_path(relative: str) -> Path | None:
    media_root = settings.media_root_path
    candidate = (media_root / relative).resolve()
    if not candidate.is_relative_to(media_root):
        return None
    return candidate


def delete_local_media_file(media_url: str | None) -> None:
    if not media_url:
        return

    relative = _relative_from_media_url(media_url)
    if relative is None:
        return

    target = _resolve_storage_path(relative)
    if target is None or not target.exists() or not target.is_file():
        return

    target.unlink(missing_ok=True)


def _infer_extension(file: UploadFile) -> str | None:
    content_type = str(file.content_type or "").lower().strip()
    if content_type in ALLOWED_IMAGE_CONTENT_TYPES:
        return ALLOWED_IMAGE_CONTENT_TYPES[content_type]

    filename = str(file.filename or "")
    suffix = Path(filename).suffix.lower().strip()
    if suffix in ALLOWED_IMAGE_EXTENSIONS:
        if suffix == ".jpeg":
            return ".jpg"
        return suffix

    return None


async def save_uploaded_producto_image(file: UploadFile) -> str:
    extension = _infer_extension(file)
    if extension is None:
        raise ValueError("Formato de imagen no permitido. Usa JPG, PNG, WEBP o GIF")

    max_bytes = int(settings.upload_max_image_size_mb) * 1024 * 1024
    if max_bytes <= 0:
        max_bytes = 5 * 1024 * 1024

    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise ValueError(f"La imagen excede el máximo permitido de {settings.upload_max_image_size_mb} MB")

    now = datetime.now(UTC)
    relative_dir = Path("productos") / now.strftime("%Y") / now.strftime("%m")
    target_dir = settings.media_root_path / relative_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid4().hex}{extension}"
    target_path = target_dir / filename
    target_path.write_bytes(content)

    relative_url = relative_dir.as_posix().strip("/")
    return f"{_public_media_prefix()}{relative_url}/{filename}"
