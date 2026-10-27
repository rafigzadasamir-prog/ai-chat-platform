"""In-memory per-user token-bucket rate limiting.

Implemented as ASGI middleware (not a route dependency) so it can inspect
and gate the raw request before any route handler runs, matching how a
real reverse-proxy-level rate limiter would behave. It only restricts the
message-sending endpoint; every other route is untouched.

The bucket store is a plain in-process dict -- appropriate for a
single-process demo app. A production, multi-process deployment would back
this with Redis instead, but the token-bucket algorithm itself is
unchanged.
"""

from __future__ import annotations

import re
import threading
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.security import InvalidTokenError, decode_access_token

_MESSAGE_ENDPOINT_RE = re.compile(r"^/conversations/\d+/messages$")


class TokenBucket:
    def __init__(self, capacity: int, refill_per_second: float) -> None:
        self.capacity = capacity
        self.refill_per_second = refill_per_second
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def try_consume(self, amount: float = 1.0) -> bool:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_per_second)
            self._last_refill = now
            if self._tokens >= amount:
                self._tokens -= amount
                return True
            return False


class RateLimiter:
    """Owns one TokenBucket per user id, created lazily on first use."""

    def __init__(self, capacity_per_minute: int) -> None:
        self.capacity_per_minute = capacity_per_minute
        self._buckets: dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def _bucket_for(self, key: str) -> TokenBucket:
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                bucket = TokenBucket(
                    capacity=self.capacity_per_minute,
                    refill_per_second=self.capacity_per_minute / 60.0,
                )
                self._buckets[key] = bucket
            return bucket

    def allow(self, key: str) -> bool:
        return self._bucket_for(key).try_consume()

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


def _extract_user_key(request: Request) -> str | None:
    """Best-effort extraction of the caller's user id from the bearer token.

    Returns None if there is no (valid) token -- in that case the request is
    let through so the downstream auth dependency can return the correct
    401, rather than the rate limiter masking it with a 429.
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.lower().startswith("bearer "):
        return None
    token = auth_header[7:].strip()
    try:
        return decode_access_token(token)
    except InvalidTokenError:
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limiter: RateLimiter) -> None:
        super().__init__(app)
        self.limiter = limiter

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "POST" and _MESSAGE_ENDPOINT_RE.match(request.url.path):
            user_key = _extract_user_key(request)
            if user_key is not None and not self.limiter.allow(user_key):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Please slow down."},
                )
        return await call_next(request)
