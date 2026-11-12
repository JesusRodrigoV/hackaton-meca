import logging
from datetime import datetime, timedelta, timezone

from redis.asyncio import Redis

from app.core.config import settings
from app.models.security import User

logger = logging.getLogger(__name__)

MAX_FAILED_ATTEMPTS = settings.MAX_FAILED_ATTEMPTS
LOCKOUT_DURATION_MINUTES = settings.LOCKOUT_DURATION_MINUTES
FAILED_ATTEMPTS_TTL_SECONDS = LOCKOUT_DURATION_MINUTES * 60
FAILED_LOGIN_PREFIX = "meca:failed_login:"

# In-memory fallback used only when Redis is not available.
_memory_failed_attempts: dict[str, dict] = {}


def _get_redis_key(identifier: str) -> str:
    return f"{FAILED_LOGIN_PREFIX}{identifier.lower().strip()}"


def _clean_expired_memory_attempts() -> None:
    now = datetime.now(timezone.utc)
    expired = [
        key
        for key, value in _memory_failed_attempts.items()
        if now - value["last_attempt"] > timedelta(seconds=FAILED_ATTEMPTS_TTL_SECONDS)
    ]
    for key in expired:
        _memory_failed_attempts.pop(key, None)


def _increment_memory(identifier: str) -> None:
    _clean_expired_memory_attempts()
    now = datetime.now(timezone.utc)
    current = _memory_failed_attempts.get(identifier)
    if current:
        current["count"] += 1
        current["last_attempt"] = now
    else:
        _memory_failed_attempts[identifier] = {"count": 1, "last_attempt": now}


async def increment_login_failure(
    email: str,
    cache: Redis | None = None,
) -> None:
    identifier = email.lower().strip()
    if cache is None:
        _increment_memory(identifier)
        return

    key = _get_redis_key(identifier)
    try:
        async with cache.pipeline() as pipe:
            await pipe.incr(key)
            await pipe.expire(key, FAILED_ATTEMPTS_TTL_SECONDS)
            await pipe.execute()
    except Exception:
        logger.exception("No se pudo incrementar fallos en Redis; usando memoria")
        _increment_memory(identifier)


async def get_login_failures(
    email: str,
    cache: Redis | None = None,
) -> int:
    identifier = email.lower().strip()
    if cache is None:
        _clean_expired_memory_attempts()
        return int(_memory_failed_attempts.get(identifier, {}).get("count", 0))

    try:
        failures = await cache.get(_get_redis_key(identifier))
        return int(failures) if failures else 0
    except Exception:
        logger.exception("No se pudieron leer fallos de Redis; usando memoria")
        _clean_expired_memory_attempts()
        return int(_memory_failed_attempts.get(identifier, {}).get("count", 0))


async def clear_login_failures(
    email: str,
    cache: Redis | None = None,
) -> None:
    identifier = email.lower().strip()
    _memory_failed_attempts.pop(identifier, None)
    if cache is None:
        return
    try:
        await cache.delete(_get_redis_key(identifier))
    except Exception:
        logger.exception("No se pudieron limpiar fallos de Redis")


def lockout_deadline() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def is_account_locked(user: User) -> bool:
    if not user.locked_until:
        return False
    return _as_utc(user.locked_until) > datetime.now(timezone.utc)


def remaining_lockout_minutes(user: User) -> int:
    if not user.locked_until:
        return 0
    remaining = _as_utc(user.locked_until) - datetime.now(timezone.utc)
    return max(1, int(remaining.total_seconds() / 60))