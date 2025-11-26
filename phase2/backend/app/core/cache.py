"""Caching utilities for API responses."""

import json
import logging
from typing import Any, Optional, Callable
from functools import wraps
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

# In-memory cache as fallback when Redis is not available
_memory_cache = {}


class CacheManager:
    """Manages caching for API responses."""
    
    def __init__(self):
        self.redis_client = None
        self.enabled = False
        
    async def initialize(self):
        """Initialize Redis connection."""
        try:
            from app.core.config import settings
            
            if not settings.CACHE_ENABLED:
                logger.info("Caching is disabled in settings")
                return
                
            try:
                import redis.asyncio as redis
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=2
                )
                # Test connection
                await self.redis_client.ping()
                self.enabled = True
                logger.info("Redis cache initialized successfully")
            except ImportError:
                logger.warning("redis package not installed, using in-memory cache")
                self.enabled = True
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using in-memory cache")
                self.enabled = True
                
        except Exception as e:
            logger.error(f"Failed to initialize cache: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.enabled:
            return None
            
        try:
            if self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                # Use in-memory cache
                if key in _memory_cache:
                    cached_data = _memory_cache[key]
                    if cached_data['expires_at'] > datetime.utcnow().timestamp():
                        return cached_data['value']
                    else:
                        del _memory_cache[key]
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL."""
        if not self.enabled:
            return False
            
        try:
            from app.core.config import settings
            ttl = ttl or settings.CACHE_TTL_SECONDS
            
            if self.redis_client:
                serialized = json.dumps(value, default=str)
                await self.redis_client.setex(key, ttl, serialized)
            else:
                # Use in-memory cache
                _memory_cache[key] = {
                    'value': value,
                    'expires_at': datetime.utcnow().timestamp() + ttl
                }
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self.enabled:
            return False
            
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
            else:
                if key in _memory_cache:
                    del _memory_cache[key]
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> bool:
        """Clear all keys matching pattern."""
        if not self.enabled:
            return False
            
        try:
            if self.redis_client:
                keys = []
                async for key in self.redis_client.scan_iter(match=pattern):
                    keys.append(key)
                if keys:
                    await self.redis_client.delete(*keys)
            else:
                # Clear matching keys from memory cache
                keys_to_delete = [k for k in _memory_cache.keys() if pattern.replace('*', '') in k]
                for key in keys_to_delete:
                    del _memory_cache[key]
            return True
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return False
    
    def generate_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from prefix and parameters."""
        # Sort kwargs for consistent key generation
        sorted_params = sorted(kwargs.items())
        params_str = json.dumps(sorted_params, default=str)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()
        return f"{prefix}:{params_hash}"


# Global cache manager instance
cache_manager = CacheManager()


def cached(ttl: Optional[int] = None, key_prefix: str = "api"):
    """Decorator for caching function results."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = cache_manager.generate_cache_key(
                f"{key_prefix}:{func.__name__}",
                args=str(args),
                kwargs=kwargs
            )
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            await cache_manager.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {cache_key}, stored result")
            
            return result
        return wrapper
    return decorator


async def invalidate_cache_pattern(pattern: str):
    """Invalidate all cache entries matching pattern."""
    await cache_manager.clear_pattern(pattern)
