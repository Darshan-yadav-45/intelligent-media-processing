"""
File validation and safe-storage helpers for uploads.
"""
import io
import uuid
from pathlib import Path

from PIL import Image as PILImage
from fastapi import UploadFile, HTTPException, status

from app.config import get_settings

settings = get_settings()

_MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def sanitize_and_build_path(original_filename: str, mime_type: str) -> tuple[str, str]:
    """Builds a safe, non-guessable filename and returns (safe_filename, absolute_path).
    Prevents path traversal by ignoring any directory component of the original name
    and generating a fresh UUID-based filename.
    """
    ext = _MIME_TO_EXT.get(mime_type)
    if not ext:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unsupported file type")

    safe_filename = f"{uuid.uuid4().hex}{ext}"
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    absolute_path = upload_dir / safe_filename
    # Defensive check: resolved path must stay within upload_dir
    if upload_dir.resolve() not in absolute_path.resolve().parents:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid file path")

    return safe_filename, str(absolute_path)


def validate_upload_size(file: UploadFile) -> int:
    """Reads the file into memory to check size; caller re-uses returned bytes.
    Rejects files over the configured limit.
    """
    contents = file.file.read()
    size = len(contents)
    if size == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Empty file")
    if size > settings.max_upload_size_bytes:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"File exceeds max size of {settings.max_upload_size_mb}MB",
        )
    file.file.seek(0)
    return size


def validate_mime_type(declared_mime: str) -> None:
    if declared_mime not in settings.allowed_mime_list:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Unsupported MIME type '{declared_mime}'. Allowed: {settings.allowed_mime_list}",
        )


def validate_actual_image_content(file_bytes: bytes) -> str:
    """Uses Pillow to sniff and verify real image content, guarding against files
    that merely have a spoofed extension/Content-Type or are corrupted.
    Returns the detected PIL format (e.g. 'JPEG', 'PNG', 'WEBP') or raises.
    """
    try:
        img = PILImage.open(io.BytesIO(file_bytes))
        img.verify()  # raises if corrupted/truncated
        detected_format = img.format
    except Exception:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "File content does not match a supported image format (corrupted or spoofed file)",
        )

    if detected_format not in ("JPEG", "PNG", "WEBP"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Unsupported detected image format '{detected_format}'",
        )
    return detected_format
