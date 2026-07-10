"""File upload storage.

Uses Cloudinary when ``CLOUDINARY_URL`` is configured (signed upload, returns a
public HTTPS URL). Otherwise falls back to local disk served by the app at
``/media/<name>`` — fine for local dev and demos, but note that Render's disk is
ephemeral, so configure Cloudinary (or another S3-compatible store) for real
KYC documents.
"""
import hashlib
import os
import re
import time
import uuid
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "application/pdf",
}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

LOCAL_DIR = Path(os.getenv("STORAGE_LOCAL_DIR", "uploads"))


class StorageError(Exception):
    pass


def _ext_for(filename: str, content_type: str) -> str:
    if "." in filename:
        return filename.rsplit(".", 1)[1].lower()[:8]
    return {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/heic": "heic",
        "application/pdf": "pdf",
    }.get(content_type, "bin")


def _cloudinary_config() -> Optional[tuple[str, str, str]]:
    url = settings.CLOUDINARY_URL
    if not url:
        return None
    m = re.match(r"cloudinary://(?P<key>[^:]+):(?P<secret>[^@]+)@(?P<cloud>.+)", url)
    if not m:
        raise StorageError("Invalid CLOUDINARY_URL format")
    return m.group("key"), m.group("secret"), m.group("cloud")


def _upload_cloudinary(data: bytes, folder: str) -> str:
    key, secret, cloud = _cloudinary_config()  # type: ignore[misc]
    timestamp = str(int(time.time()))
    # Signature: sorted params joined by & then api_secret, sha1 hex.
    to_sign = f"folder={folder}&timestamp={timestamp}{secret}"
    signature = hashlib.sha1(to_sign.encode()).hexdigest()
    resp = httpx.post(
        f"https://api.cloudinary.com/v1_1/{cloud}/auto/upload",
        data={"api_key": key, "timestamp": timestamp, "folder": folder, "signature": signature},
        files={"file": data},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["secure_url"]


def _upload_local(data: bytes, ext: str) -> str:
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.{ext}"
    (LOCAL_DIR / name).write_bytes(data)
    base = settings.BACKEND_URL.rstrip("/")
    return f"{base}/media/{name}"


def upload_bytes(data: bytes, filename: str, content_type: str, folder: str = "homekeeper") -> str:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise StorageError("Unsupported file type")
    if len(data) > MAX_UPLOAD_BYTES:
        raise StorageError("File too large (max 10 MB)")
    if _cloudinary_config():
        return _upload_cloudinary(data, folder)
    return _upload_local(data, _ext_for(filename, content_type))
