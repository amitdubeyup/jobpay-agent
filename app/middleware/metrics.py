"""
Metrics collection middleware.
"""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

from app.monitoring import metrics

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect request metrics and performance data.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Start timing
        start_time = time.time()
        metrics.increment_active_requests()
        
        # Get user info if available
        user_id = None
        if hasattr(request.state, 'user') and request.state.user:
            user_id = getattr(request.state.user, 'id', None)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            metrics.record_request(
                endpoint=request.url.path,
                method=request.method,
                duration=duration,
                status_code=response.status_code,
                user_id=user_id
            )
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            response.headers["X-Request-ID"] = str(id(request))
            
            return response
            
        except Exception as e:
            # Record error
            duration = time.time() - start_time
            metrics.record_request(
                endpoint=request.url.path,
                method=request.method,
                duration=duration,
                status_code=500,
                user_id=user_id
            )
            
            logger.error(f"Request failed: {e}")
            raise
        
        finally:
            metrics.decrement_active_requests()
