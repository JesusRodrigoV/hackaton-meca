from slowapi import Limiter
from app.core.request_context import resolve_client_ip

def get_render_remote_address(request) -> str:
    """Resuelve la IP real tras el balanceador de carga de Render."""
    return resolve_client_ip(request) or "127.0.0.1"

limiter = Limiter(key_func=get_render_remote_address)