from functools import lru_cache
from typing import Any

from services.api.core.config import get_settings


class MemoryRedis:
    """In-process Redis fallback for local dev without Redis."""

    def __init__(self) -> None:
        self._lists: dict[str, list[str]] = {}
        self._ttl: dict[str, int] = {}

    async def lrange(self, key: str, start: int, end: int) -> list[str]:
        items = self._lists.get(key, [])
        return items[start : end + 1 if end >= 0 else None]

    async def rpush(self, key: str, value: str) -> None:
        self._lists.setdefault(key, []).append(value)

    async def expire(self, key: str, seconds: int) -> None:
        self._ttl[key] = seconds


_memory: MemoryRedis | None = None


@lru_cache
def get_redis() -> Any:
    global _memory
    settings = get_settings()
    if "sqlite" in settings.database_url:
        if _memory is None:
            _memory = MemoryRedis()
        return _memory
    try:
        import redis.asyncio as redis

        return redis.from_url(settings.redis_url, decode_responses=True)
    except Exception:
        if _memory is None:
            _memory = MemoryRedis()
        return _memory
