"""Fixed-window rate limiting on Redis.

Behind a reverse proxy, run uvicorn with ``--proxy-headers
--forwarded-allow-ips=<proxy ip>`` so ``request.client.host`` is the real
client and not the proxy (otherwise every user shares one bucket).
"""
import logging

from fastapi import HTTPException
from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# One shared client, built from config. Lazily connects on first use.
redis_client = Redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)


async def hit(key: str, limit: int, window_seconds: int, detail: str) -> None:
    """Count one request against ``key``; raise 429 past ``limit`` per window.

    INCR first, then compare, so concurrent requests can't all slip under the
    threshold. Fail-open when Redis is unreachable: availability over a
    best-effort guard (logged so an operator notices).
    """
    try:
        count = await redis_client.incr(f"rate_limit:{key}")
        if count == 1:
            await redis_client.expire(f"rate_limit:{key}", window_seconds)
    except Exception:
        logger.warning("Rate limiter unavailable (Redis down?); allowing %s.", key)
        return
    if count > limit:
        raise HTTPException(status_code=429, detail=detail)
