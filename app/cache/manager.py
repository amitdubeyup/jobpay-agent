"""
Redis-based caching implementation for the JobPay Agent.

SECURITY NOTE: This module uses JSON serialization only.
Pickle has been intentionally removed due to security risks
(arbitrary code execution via malicious pickled objects).
"""

import json
from typing import Any, Optional, Union, Dict, List
from datetime import timedelta, datetime, date
from decimal import Decimal
import redis
import logging
from functools import wraps
import hashlib

from app.core.config import settings
from app.constants import (
    CACHE_TTL_SHORT,
    CACHE_TTL_MEDIUM,
    CACHE_TTL_LONG,
    CACHE_TTL_DAILY
)

logger = logging.getLogger(__name__)


class SafeJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles common Python types safely.
    Replaces pickle for serialization of complex objects.
    """

    def default(self, obj):
        if isinstance(obj, datetime):
            return {"__type__": "datetime", "value": obj.isoformat()}
        if isinstance(obj, date):
            return {"__type__": "date", "value": obj.isoformat()}
        if isinstance(obj, Decimal):
            return {"__type__": "decimal", "value": str(obj)}
        if isinstance(obj, bytes):
            return {"__type__": "bytes", "value": obj.decode('utf-8', errors='replace')}
        if isinstance(obj, set):
            return {"__type__": "set", "value": list(obj)}
        if hasattr(obj, '__dict__'):
            return {"__type__": "object", "class": obj.__class__.__name__, "value": obj.__dict__}
        return super().default(obj)


def safe_json_decoder(obj):
    """
    Custom JSON decoder that restores special types.
    """
    if isinstance(obj, dict) and "__type__" in obj:
        type_name = obj["__type__"]
        value = obj["value"]

        if type_name == "datetime":
            return datetime.fromisoformat(value)
        if type_name == "date":
            return date.fromisoformat(value)
        if type_name == "decimal":
            return Decimal(value)
        if type_name == "bytes":
            return value.encode('utf-8')
        if type_name == "set":
            return set(value)
        # For objects, return as dict (cannot reconstruct class instances safely)
        if type_name == "object":
            return value
    return obj


class CacheManager:
    """
    Redis-based cache manager with fallback to in-memory cache.

    SECURITY: Uses JSON serialization only - no pickle allowed.
    """

    def __init__(self):
        self.redis_client = None
        self.memory_cache: Dict[str, Any] = {}
        self.memory_cache_ttl: Dict[str, float] = {}
        self._connect_redis()
    
    def _connect_redis(self):
        """Connect to Redis with fallback handling."""
        try:
            if settings.REDIS_URL:
                # Handle SSL connections for Upstash Redis
                redis_config = {
                    'decode_responses': True,
                    'socket_timeout': 5,
                    'socket_connect_timeout': 5,
                    'retry_on_timeout': True
                }
                
                # If using rediss:// (SSL), add SSL configuration
                if settings.REDIS_URL.startswith('rediss://'):
                    redis_config.update({
                        'ssl_cert_reqs': None,  # Don't require certificate verification for Upstash
                        'ssl_check_hostname': False,
                        'ssl_ca_certs': None
                    })
                
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    **redis_config
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Connected to Redis cache")
            else:
                logger.warning("Redis URL not configured, using memory cache")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using memory cache fallback")
            self.redis_client = None
    
    def _generate_key(self, namespace: str, key: str, **kwargs) -> str:
        """Generate a cache key with namespace and optional parameters."""
        key_parts = [namespace, key]
        
        # Add sorted kwargs to ensure consistent key generation
        if kwargs:
            params_str = "&".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
            key_parts.append(params_str)
        
        full_key = ":".join(key_parts)
        
        # Hash long keys to prevent Redis key length issues
        if len(full_key) > 250:
            return f"{namespace}:{hashlib.md5(full_key.encode()).hexdigest()}"
        
        return full_key
    
    def get(self, namespace: str, key: str, **kwargs) -> Optional[Any]:
        """Get value from cache using JSON deserialization only."""
        cache_key = self._generate_key(namespace, key, **kwargs)

        # Try Redis first
        if self.redis_client:
            try:
                value = self.redis_client.get(cache_key)
                if value is not None:
                    try:
                        return json.loads(value, object_hook=safe_json_decoder)
                    except json.JSONDecodeError as e:
                        # Log and return None for corrupted/invalid cache entries
                        logger.warning(f"Invalid JSON in cache for key {cache_key}: {e}")
                        # Delete the corrupted entry
                        self.redis_client.delete(cache_key)
                        return None
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
        
        # Fallback to memory cache
        if cache_key in self.memory_cache:
            import time
            if cache_key in self.memory_cache_ttl:
                if time.time() > self.memory_cache_ttl[cache_key]:
                    # Expired
                    del self.memory_cache[cache_key]
                    del self.memory_cache_ttl[cache_key]
                    return None
            return self.memory_cache[cache_key]
        
        return None
    
    def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl: int = CACHE_TTL_MEDIUM,
        **kwargs
    ) -> bool:
        """Set value in cache with TTL using JSON serialization only."""
        cache_key = self._generate_key(namespace, key, **kwargs)

        # Try Redis first
        if self.redis_client:
            try:
                # Use SafeJSONEncoder for all objects
                serialized_value = json.dumps(value, cls=SafeJSONEncoder)
                self.redis_client.setex(cache_key, ttl, serialized_value)
                return True
            except (TypeError, ValueError) as e:
                # Object cannot be serialized to JSON
                logger.warning(f"Cannot serialize value for key {cache_key}: {e}")
                logger.warning("Consider making the object JSON-serializable")
                return False
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
        
        # Fallback to memory cache
        import time
        self.memory_cache[cache_key] = value
        self.memory_cache_ttl[cache_key] = time.time() + ttl
        return True
    
    def delete(self, namespace: str, key: str, **kwargs) -> bool:
        """Delete value from cache."""
        cache_key = self._generate_key(namespace, key, **kwargs)
        
        # Try Redis first
        if self.redis_client:
            try:
                self.redis_client.delete(cache_key)
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
        
        # Memory cache
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]
        if cache_key in self.memory_cache_ttl:
            del self.memory_cache_ttl[cache_key]
        
        return True
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        deleted_count = 0
        
        # Try Redis first
        if self.redis_client:
            try:
                keys = self.redis_client.keys(pattern)
                if keys:
                    deleted_count = self.redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis delete pattern error: {e}")
        
        # Memory cache
        keys_to_delete = [k for k in self.memory_cache.keys() if pattern.replace('*', '') in k]
        for key in keys_to_delete:
            del self.memory_cache[key]
            if key in self.memory_cache_ttl:
                del self.memory_cache_ttl[key]
            deleted_count += 1
        
        return deleted_count
    
    def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace."""
        return self.delete_pattern(f"{namespace}:*")


# Global cache instance
cache = CacheManager()


def cached(
    namespace: str, 
    ttl: int = CACHE_TTL_MEDIUM,
    key_func: Optional[callable] = None
):
    """
    Decorator for caching function results.
    
    Args:
        namespace: Cache namespace
        ttl: Time to live in seconds
        key_func: Function to generate cache key from args/kwargs
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                if args:
                    key_parts.extend([str(arg) for arg in args])
                if kwargs:
                    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = cache.get(namespace, cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {namespace}:{cache_key}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {namespace}:{cache_key}")
            result = await func(*args, **kwargs)
            
            # Cache the result
            cache.set(namespace, cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                if args:
                    key_parts.extend([str(arg) for arg in args])
                if kwargs:
                    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = cache.get(namespace, cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {namespace}:{cache_key}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {namespace}:{cache_key}")
            result = func(*args, **kwargs)
            
            # Cache the result
            cache.set(namespace, cache_key, result, ttl)
            
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Cache invalidation helpers
def invalidate_user_cache(user_id: int):
    """Invalidate all cache entries for a specific user."""
    cache.delete_pattern(f"user:{user_id}:*")
    cache.delete_pattern(f"users:*")


def invalidate_job_cache(job_id: int = None):
    """Invalidate job-related cache entries."""
    if job_id:
        cache.delete_pattern(f"job:{job_id}:*")
    cache.delete_pattern(f"jobs:*")


def invalidate_matching_cache(user_id: int = None):
    """Invalidate job matching cache entries."""
    if user_id:
        cache.delete_pattern(f"matching:{user_id}:*")
    cache.delete_pattern(f"matching:*")


# Pre-defined cache namespaces and TTLs
class CacheNamespaces:
    USERS = "users"
    JOBS = "jobs"
    MATCHING = "matching"
    NOTIFICATIONS = "notifications"
    AUTH = "auth"
    ANALYTICS = "analytics"


class CacheTTL:
    SHORT = CACHE_TTL_SHORT      # 5 minutes
    MEDIUM = CACHE_TTL_MEDIUM    # 30 minutes  
    LONG = CACHE_TTL_LONG        # 1 hour
    DAILY = CACHE_TTL_DAILY      # 24 hours
