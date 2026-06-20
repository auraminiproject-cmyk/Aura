"""Object storage — local filesystem or MinIO (S3-compatible). No Cloudflare R2."""

import logging
import uuid
from pathlib import Path

import httpx

from services.api.core.config import get_settings

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.backend = self.settings.storage_backend.lower()
        self.local_root = Path(self.settings.storage_local_path)
        if self.backend == "local":
            self.local_root.mkdir(parents=True, exist_ok=True)

    async def upload_bytes(
        self,
        data: bytes,
        *,
        key: str | None = None,
        content_type: str = "application/octet-stream",
    ) -> str:
        object_key = key or f"{uuid.uuid4()}"
        if self.backend == "local":
            return self._save_local(object_key, data)
        if self.backend == "minio":
            return await self._save_minio(object_key, data, content_type)
        return self._save_local(object_key, data)

    def _save_local(self, key: str, data: bytes) -> str:
        path = self.local_root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return f"/api/v1/storage/{key}"

    async def _save_minio(self, key: str, data: bytes, content_type: str) -> str:
        settings = self.settings
        url = f"{settings.s3_endpoint.rstrip('/')}/{settings.s3_bucket}/{key}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.put(
                url,
                content=data,
                headers={"Content-Type": content_type},
                auth=(settings.s3_access_key, settings.s3_secret_key),
            )
            resp.raise_for_status()
        return url

    def read_local(self, key: str) -> bytes | None:
        path = self.local_root / key
        if path.is_file():
            return path.read_bytes()
        return None


def get_storage() -> StorageService:
    return StorageService()
