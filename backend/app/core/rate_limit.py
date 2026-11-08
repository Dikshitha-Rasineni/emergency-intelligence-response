"""Small in-process sliding-window rate limiter (per client IP).
Single-process only; use a Redis-backed limiter when running several workers."""
import time
from collections import defaultdict, deque
from threading import Lock
from fastapi import HTTPException, Request, status

_buckets: dict = defaultdict(deque)
_lock = Lock()


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def check_rate(request: Request, key: str, limit_per_min: int) -> None:
    if limit_per_min <= 0:
        return
    now = time.monotonic()
    bucket_key = (key, client_ip(request))
    with _lock:
        q = _buckets[bucket_key]
        while q and now - q[0] > 60.0:
            q.popleft()
        if len(q) >= limit_per_min:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"error": "RATE_LIMITED", "message": "Too many requests. If this is an emergency, call 112."},
            )
        q.append(now)


def reset_all() -> None:
    with _lock:
        _buckets.clear()
