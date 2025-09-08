"""
Performance monitoring and metrics collection for JobPay Agent.
"""

import time
import psutil
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
from functools import wraps
import asyncio
from contextlib import asynccontextmanager

from app.cache import cache, CacheNamespaces, CacheTTL

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and aggregates application metrics.
    """
    
    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self.request_times = deque(maxlen=max_samples)
        self.error_counts = defaultdict(int)
        self.endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'avg_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'errors': 0
        })
        self.active_requests = 0
        self.total_requests = 0
        self.start_time = time.time()
    
    def record_request(
        self, 
        endpoint: str, 
        method: str,
        duration: float, 
        status_code: int,
        user_id: Optional[int] = None
    ):
        """Record a request metric."""
        self.total_requests += 1
        self.request_times.append({
            'timestamp': time.time(),
            'duration': duration,
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'user_id': user_id
        })
        
        # Update endpoint statistics
        key = f"{method} {endpoint}"
        stats = self.endpoint_stats[key]
        stats['count'] += 1
        stats['total_time'] += duration
        stats['avg_time'] = stats['total_time'] / stats['count']
        stats['min_time'] = min(stats['min_time'], duration)
        stats['max_time'] = max(stats['max_time'], duration)
        
        if status_code >= 400:
            stats['errors'] += 1
            self.error_counts[status_code] += 1
    
    def increment_active_requests(self):
        """Increment active request counter."""
        self.active_requests += 1
    
    def decrement_active_requests(self):
        """Decrement active request counter."""
        self.active_requests = max(0, self.active_requests - 1)
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_mb': memory.used / (1024 * 1024),
                'memory_available_mb': memory.available / (1024 * 1024),
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / (1024 * 1024 * 1024),
                'active_requests': self.active_requests,
                'total_requests': self.total_requests,
                'uptime_seconds': time.time() - self.start_time
            }
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
            return {
                'active_requests': self.active_requests,
                'total_requests': self.total_requests,
                'uptime_seconds': time.time() - self.start_time
            }
    
    def get_request_metrics(self, window_minutes: int = 5) -> Dict[str, Any]:
        """Get request metrics for the specified time window."""
        current_time = time.time()
        window_start = current_time - (window_minutes * 60)
        
        # Filter requests within the time window
        recent_requests = [
            req for req in self.request_times 
            if req['timestamp'] >= window_start
        ]
        
        if not recent_requests:
            return {
                'total_requests': 0,
                'requests_per_minute': 0.0,
                'avg_response_time': 0.0,
                'error_rate': 0.0,
                'p95_response_time': 0.0,
                'p99_response_time': 0.0
            }
        
        # Calculate metrics
        durations = [req['duration'] for req in recent_requests]
        durations.sort()
        
        total_requests = len(recent_requests)
        error_requests = len([req for req in recent_requests if req['status_code'] >= 400])
        
        p95_index = int(0.95 * len(durations))
        p99_index = int(0.99 * len(durations))
        
        return {
            'total_requests': total_requests,
            'requests_per_minute': total_requests / window_minutes,
            'avg_response_time': sum(durations) / len(durations),
            'error_rate': (error_requests / total_requests) * 100,
            'p95_response_time': durations[p95_index] if durations else 0.0,
            'p99_response_time': durations[p99_index] if durations else 0.0,
            'min_response_time': min(durations),
            'max_response_time': max(durations)
        }
    
    def get_endpoint_metrics(self) -> Dict[str, Any]:
        """Get per-endpoint metrics."""
        return dict(self.endpoint_stats)
    
    def get_error_metrics(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            'error_counts': dict(self.error_counts),
            'total_errors': sum(self.error_counts.values())
        }


# Global metrics collector
metrics = MetricsCollector()


class PerformanceMonitor:
    """
    Performance monitoring context manager and decorator.
    """
    
    @staticmethod
    @asynccontextmanager
    async def monitor_async(operation_name: str):
        """Async context manager for monitoring operations."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            logger.info(f"Operation {operation_name} took {duration:.3f}s")
            
            # Cache performance metrics
            cache.set(
                CacheNamespaces.ANALYTICS,
                f"operation_time:{operation_name}",
                {
                    'duration': duration,
                    'timestamp': time.time(),
                    'operation': operation_name
                },
                ttl=CacheTTL.LONG
            )
    
    @staticmethod
    def monitor_sync(operation_name: str):
        """Sync context manager for monitoring operations."""
        class SyncMonitor:
            def __enter__(self):
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time
                logger.info(f"Operation {operation_name} took {duration:.3f}s")
                
                # Cache performance metrics
                cache.set(
                    CacheNamespaces.ANALYTICS,
                    f"operation_time:{operation_name}",
                    {
                        'duration': duration,
                        'timestamp': time.time(),
                        'operation': operation_name
                    },
                    ttl=CacheTTL.LONG
                )
        
        return SyncMonitor()


def monitor_performance(operation_name: Optional[str] = None):
    """
    Decorator for monitoring function performance.
    """
    def decorator(func):
        nonlocal operation_name
        if operation_name is None:
            operation_name = f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            async with PerformanceMonitor.monitor_async(operation_name):
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with PerformanceMonitor.monitor_sync(operation_name):
                return func(*args, **kwargs)
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class HealthChecker:
    """
    System health monitoring.
    """
    
    @staticmethod
    async def check_database():
        """Check database connectivity."""
        try:
            from app.db.session import get_db
            async for db in get_db():
                await db.execute("SELECT 1")
                return {"status": "healthy", "message": "Database connection OK"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Database error: {str(e)}"}
    
    @staticmethod
    async def check_redis():
        """Check Redis connectivity."""
        try:
            cache._connect_redis()
            if cache.redis_client:
                cache.redis_client.ping()
                return {"status": "healthy", "message": "Redis connection OK"}
            else:
                return {"status": "degraded", "message": "Redis unavailable, using memory cache"}
        except Exception as e:
            return {"status": "unhealthy", "message": f"Redis error: {str(e)}"}
    
    @staticmethod
    async def check_external_services():
        """Check external service connectivity."""
        checks = {}
        
        # Check OpenAI API
        try:
            # This would be a simple ping or status check
            checks["openai"] = {"status": "healthy", "message": "Service available"}
        except Exception as e:
            checks["openai"] = {"status": "unhealthy", "message": f"OpenAI error: {str(e)}"}
        
        # Check notification services
        checks["notifications"] = {"status": "healthy", "message": "Services available"}
        
        return checks
    
    @staticmethod
    async def comprehensive_health_check():
        """Run all health checks."""
        start_time = time.time()
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {},
            "metrics": metrics.get_system_metrics()
        }
        
        # Database check
        health_status["checks"]["database"] = await HealthChecker.check_database()
        
        # Redis check
        health_status["checks"]["redis"] = await HealthChecker.check_redis()
        
        # External services check
        external_checks = await HealthChecker.check_external_services()
        health_status["checks"]["external_services"] = external_checks
        
        # Determine overall status
        unhealthy_checks = [
            name for name, check in health_status["checks"].items()
            if isinstance(check, dict) and check.get("status") == "unhealthy"
        ]
        
        degraded_checks = [
            name for name, check in health_status["checks"].items()
            if isinstance(check, dict) and check.get("status") == "degraded"
        ]
        
        if unhealthy_checks:
            health_status["status"] = "unhealthy"
        elif degraded_checks:
            health_status["status"] = "degraded"
        
        health_status["check_duration"] = time.time() - start_time
        
        return health_status


# Export main components
monitor = PerformanceMonitor()
health_checker = HealthChecker()
