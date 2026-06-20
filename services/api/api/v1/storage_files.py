from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from services.api.core.storage import get_storage

router = APIRouter()


@router.get("/{key:path}")
async def get_stored_file(key: str):
    storage = get_storage()
    if storage.backend != "local":
        raise HTTPException(status_code=501, detail="Direct file serve only for local storage")
    data = storage.read_local(key)
    if data is None:
        raise HTTPException(status_code=404, detail="Not found")
    content_type = "image/jpeg" if key.lower().endswith((".jpg", ".jpeg")) else "application/octet-stream"
    return Response(content=data, media_type=content_type)
