import logging
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)

_cache_client: redis.Redis | None = None

async def get_cache_client() -> redis.Redis | None:
    global _cache_client
    if _cache_client is not None:
        return _cache_client
    
    try:
        pool = redis.ConnectionPool.from_url(
            settings.redis_connection_url,
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0
        )
        _cache_client = redis.Redis.from_pool(pool)
        logger.info("Conectado a Redis en %s", settings.redis_connection_url)
        return _cache_client
    except Exception as e:
        logger.error("No se pudo conectar a Redis en %s: %s", settings.redis_connection_url, e)
        return None

async def ping_redis():
    client = await get_cache_client()
    if not client:
        return False
    try:
        await client.ping()
        return True
    except Exception:
        return False
