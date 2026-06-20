"""Rate limiter — per-user (JWT) for authenticated routes, per-IP for anonymous."""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _user_or_ip_key(request: Request) -> str:
    """Extract user ID from JWT Authorization header, fallback to IP."""
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        try:
            from services.api.core.security import decode_token
            payload = decode_token(auth.split(" ", 1)[1])
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except Exception:
            pass
    return get_remote_address(request)


limiter = Limiter(key_func=_user_or_ip_key, default_limits=["30/minute"])
