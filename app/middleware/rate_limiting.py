"""
Rate limiting middleware for API protection.
"""

from typing import Callable
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import time
import redis
from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent API abuse.
    Uses Redis for distributed rate limiting.
    """

    def __init__(self, app, calls_per_minute: int = None):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.redis_client = None
        try:
            # Try to connect to Redis, fall back to in-memory if not available
            self.redis_client = redis.from_url(settings.REDIS_URL)
            self.redis_client.ping()
        except Exception:
            # Fall back to in-memory storage for development
            self._memory_store = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and apply rate limiting.
        """
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        current_time = int(time.time())
        window_start = current_time - 60  # 1-minute window

        if self._is_rate_limited(client_ip, window_start, current_time):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.calls_per_minute} requests per minute."
            )

        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host

    def _is_rate_limited(self, client_ip: str, window_start: int, current_time: int) -> bool:
        """Check if the client has exceeded the rate limit."""
        key = f"rate_limit:{client_ip}"

        if self.redis_client:
            return self._check_redis_rate_limit(key, window_start, current_time)
        else:
            return self._check_memory_rate_limit(key, window_start, current_time)

    def _check_redis_rate_limit(self, key: str, window_start: int, current_time: int) -> bool:
        """Check rate limit using Redis."""
        try:
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.expire(key, 60)
            results = pipe.execute()
            
            request_count = results[1]
            return request_count >= self.calls_per_minute
        except Exception:
            # If Redis fails, allow the request
            return False

    def _check_memory_rate_limit(self, key: str, window_start: int, current_time: int) -> bool:
        """Check rate limit using in-memory storage (development only)."""
        if key not in self._memory_store:
            self._memory_store[key] = []

        # Remove old entries
        self._memory_store[key] = [
            timestamp for timestamp in self._memory_store[key]
            if timestamp > window_start
        ]

        # Add current request
        self._memory_store[key].append(current_time)

        return len(self._memory_store[key]) > self.calls_per_minute
