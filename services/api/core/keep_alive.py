"""Self-ping to prevent Render free-tier sleep (every 10 min)."""

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

_PING_INTERVAL = 600  # 10 minutes
_SELF_URL = "https://aura-0cet.onrender.com/health"


async def keep_alive_loop() -> None:
    """Background coroutine that pings /health to prevent Render sleep."""
    logger.info("Keep-alive loop started (interval=%ds)", _PING_INTERVAL)
    while True:
        await asyncio.sleep(_PING_INTERVAL)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(_SELF_URL)
                logger.debug("Keep-alive ping: %d", resp.status_code)
        except Exception as exc:
            logger.warning("Keep-alive ping failed: %s", exc)
