"""Authenticated file upload endpoint (returns a stored URL)."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.deps import get_current_user
from app.models.user import User
from app.services.storage import StorageError, upload_bytes

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload(
    file: UploadFile = File(...),
    folder: str = "homekeeper",
    user: User = Depends(get_current_user),
):
    data = await file.read()
    try:
        url = upload_bytes(data, file.filename or "upload", file.content_type or "application/octet-stream", folder)
    except StorageError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except Exception:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Upload failed")
    return {"url": url}
