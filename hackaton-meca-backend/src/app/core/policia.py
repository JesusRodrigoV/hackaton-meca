import logging
from sqlalchemy.orm import Session
from redis.asyncio import Redis
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

from app.db.session import SessionLocal
from app.models.user import User
from app.db.cache import get_cache_client
from fastapi import Depends


MAX_FAILED_ATTEMPTS = 5
# tiempo bloqueo
LOCKOUT_DURATION_MINUTES = 5 
# Cuanto va recordar redis el tiempo de bloqueo
FAILED_ATTEMPTS_TTL_SECONDS = 300

FAILED_LOGIN_PREFIX = "failed_login:"

# In-memory dictionary fallback to store failed attempts with timestamp
# Format: {identifier: {"count": int, "last_attempt": datetime}}
_memory_failed_attempts = {}


def _get_redis_key(identifier: str) -> str:
    """Generar clave redis"""
    return f"{FAILED_LOGIN_PREFIX}{identifier.lower().strip()}"


def _clean_expired_memory_attempts():
    """Limpia los intentos de inicio de sesión expirados en memoria"""
    now = datetime.now(timezone.utc)
    expired_keys = []
    for k, v in _memory_failed_attempts.items():
        if now - v["last_attempt"] > timedelta(seconds=FAILED_ATTEMPTS_TTL_SECONDS):
            expired_keys.append(k)
    for k in expired_keys:
        if k in _memory_failed_attempts:
            del _memory_failed_attempts[k]


async def increment_login_failure(
    email: str,
    cache: Redis = Depends(get_cache_client)
):
    """
    Incrementa el contador de fallos para un identificador en Redis (con fallback en memoria)
    """
    identifier = email.lower().strip()
    if not cache:
        logger.warning("Cliente Redis no disponible. Usando fallback en memoria para increment_login_failure")
        _clean_expired_memory_attempts()
        now = datetime.now(timezone.utc)
        if identifier in _memory_failed_attempts:
            _memory_failed_attempts[identifier]["count"] += 1
            _memory_failed_attempts[identifier]["last_attempt"] = now
        else:
            _memory_failed_attempts[identifier] = {"count": 1, "last_attempt": now}
        return

    key = _get_redis_key(email)
    try:
        async with cache.pipeline() as pipe:
            await pipe.incr(key)
            await pipe.expire(key, FAILED_ATTEMPTS_TTL_SECONDS)
            await pipe.execute()
    except Exception as e:
        logger.error("Error al incrementar fallos en Redis: %s. Usando fallback en memoria", e)
        _clean_expired_memory_attempts()
        now = datetime.now(timezone.utc)
        if identifier in _memory_failed_attempts:
            _memory_failed_attempts[identifier]["count"] += 1
            _memory_failed_attempts[identifier]["last_attempt"] = now
        else:
            _memory_failed_attempts[identifier] = {"count": 1, "last_attempt": now}


async def get_login_failures(
    email: str,
    cache: Redis = Depends(get_cache_client)
) -> int:
    """
    Obtiene el numero de fallos acumulados (con fallback en memoria)
    """
    identifier = email.lower().strip()
    if not cache:
        logger.warning("Cliente Redis no disponible. Usando fallback en memoria para get_login_failures")
        _clean_expired_memory_attempts()
        return _memory_failed_attempts.get(identifier, {}).get("count", 0)

    key = _get_redis_key(email)
    try:
        failures = await cache.get(key)
        return int(failures) if failures else 0
    except Exception as e:
        logger.error("Error al obtener fallos de Redis: %s. Usando fallback en memoria", e)
        _clean_expired_memory_attempts()
        return _memory_failed_attempts.get(identifier, {}).get("count", 0)


async def clear_login_failures(
    email: str,
    cache: Redis = Depends(get_cache_client)
):
    """
    Limpia el contador de fallos (con fallback en memoria)
    """
    identifier = email.lower().strip()
    if not cache:
        logger.warning("Cliente Redis no disponible. Usando fallback en memoria para clear_login_failures")
        if identifier in _memory_failed_attempts:
            del _memory_failed_attempts[identifier]
        return
        
    key = _get_redis_key(email)
    try:
        await cache.delete(key)
    except Exception as e:
        logger.error("Error al borrar fallos de Redis: %s. Usando fallback en memoria", e)
        if identifier in _memory_failed_attempts:
            del _memory_failed_attempts[identifier]


def lock_account(user_id: str) -> None:
    """
    Escribe el bloqueo oficial en la base de datos
    """
    db: Session = SessionLocal()
    try:
        # Búsqueda ultra robusta por ID, username o email para soportar cualquier identificador
        user = db.query(User).filter(
            (User.id == user_id) | 
            (User.username == user_id) | 
            (User.email == user_id)
        ).first()
        
        if user:
            lock_until_time = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            user.locked_until = lock_until_time
            db.add(user)
            db.commit()
            logger.info("Cuenta del usuario %s bloqueada exitosamente hasta %s", user.id, lock_until_time)
    except Exception as e:
        logger.exception("Error en background task (lock_account) para %s", user_id)
        db.rollback()
    finally:
        db.close()


def is_account_locked(user: User) -> bool:
    """
    Verifica de forma segura y compatible con zonas horarias si la cuenta está bloqueada
    """
    if not user.locked_until:
        return False

    locked_until = user.locked_until
    # Soporte para base de datos con datetimes naive (sin zona horaria)
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)

    return locked_until > datetime.now(timezone.utc)
