from contextvars import ContextVar
from typing import Optional

from fastapi import Request


current_client_ip: ContextVar[Optional[str]] = ContextVar("current_client_ip", default=None)


def resolve_client_ip(request: Request) -> Optional[str]:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip() or None

    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip() or None

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip() or None

    return request.client.host if request.client else None
