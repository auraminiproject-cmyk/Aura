import pytest

from services.api.core.storage import StorageService


@pytest.mark.asyncio
async def test_local_storage_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("STORAGE_LOCAL_PATH", str(tmp_path))
    from services.api.core.config import get_settings

    get_settings.cache_clear()

    storage = StorageService()
    url = await storage.upload_bytes(b"test-data", key="test/file.bin")
    assert "/api/v1/storage/" in url
    assert storage.read_local("test/file.bin") == b"test-data"

    get_settings.cache_clear()
