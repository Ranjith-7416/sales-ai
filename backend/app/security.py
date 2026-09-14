"""Authentication and request rate limiting dependencies."""
import secrets
import time
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.services.cache_service import get_cache_service

_bearer = HTTPBearer(auto_error=False)


def _configured_auth_token() -> str | None:
    token = (settings.API_AUTH_TOKEN or "").strip()
    if not token or token.lower().startswith(("your-", "your_", "<")):
        return None
    return token


async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    expected = _configured_auth_token()
    if expected is None:
        if settings.ENVIRONMENT.lower() == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="API authentication is not configured in production",
            )
        return
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not secrets.compare_digest(credentials.credentials, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def rate_limit(setting_name: str) -> Callable:
    async def dependency(request: Request) -> None:
        limit = max(1, int(getattr(settings, setting_name)))
        window = max(1, int(settings.RATE_LIMIT_WINDOW_SECONDS))
        client_host = request.client.host if request.client else "unknown"
        key = f"rate-limit:{request.url.path}:{client_host}"
        cache = get_cache_service()

        if cache.redis_client:
            count = cache.redis_client.incr(key)
            if count == 1:
                cache.redis_client.expire(key, window)
        else:
            now = time.monotonic()
            entry = cache.in_memory_cache.get(key)
            if not entry or now >= entry["expires_at"]:
                entry = {"count": 0, "expires_at": now + window}
            entry["count"] += 1
            cache.in_memory_cache[key] = entry
            count = entry["count"]

        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Application rate limit exceeded",
                headers={"Retry-After": str(window)},
            )

    return dependency
