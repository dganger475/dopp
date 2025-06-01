"""
Cache Configuration
=================

Configures caching with Redis support and fallback to simple cache.
"""

from flask_caching import Cache
from functools import wraps
from flask import request, current_app
import functools
from typing import Any, Callable, Optional
from datetime import datetime, timedelta

# Initialize cache
cache = Cache()

# In-memory cache for development
_cache = {}
_cache_timeouts = {}

def setup_cache(app):
    """Configure caching for the application"""
    cache_config = {
        'CACHE_TYPE': app.config.get('CACHE_TYPE', 'simple'),
        'CACHE_DEFAULT_TIMEOUT': app.config.get('CACHE_DEFAULT_TIMEOUT', 300)
    }
    
    # Configure Redis if available
    if app.config.get('CACHE_TYPE') == 'redis':
        cache_config.update({
            'CACHE_REDIS_URL': app.config.get('CACHE_REDIS_URL'),
            'CACHE_KEY_PREFIX': 'dopp:',
            'CACHE_OPTIONS': {
                'socket_timeout': 2,
                'socket_connect_timeout': 2,
                'retry_on_timeout': True,
                'max_connections': 50
            }
        })
    
    cache.init_app(app, config=cache_config)
    return cache

def cached_with_key(*args, **kwargs):
    """Custom cache decorator with dynamic key generation"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = _generate_cache_key(f, *args, **kwargs)
            rv = cache.get(cache_key)
            if rv is not None:
                return rv
            rv = f(*args, **kwargs)
            cache.set(cache_key, rv)
            return rv
        return decorated_function
    return decorator

def _generate_cache_key(f, *args, **kwargs):
    """Generate a unique cache key based on function and arguments"""
    key_parts = [
        f.__module__,
        f.__name__,
        str(args),
        str(sorted(kwargs.items())),
    ]
    
    # Add user-specific data if available
    if hasattr(request, 'user_id'):
        key_parts.append(str(request.user_id))
    
    return ':'.join(key_parts)

def invalidate_cache_pattern(pattern):
    """Invalidate all cache keys matching a pattern"""
    if hasattr(cache, 'delete_pattern'):
        cache.delete_pattern(pattern)
    else:
        # Fallback for simple cache
        keys = [k for k in cache.cache._cache.keys() if pattern in k]
        for key in keys:
            cache.delete(key)

def get_cache_stats():
    """Get cache statistics"""
    stats = {
        'type': current_app.config.get('CACHE_TYPE'),
        'timeout': current_app.config.get('CACHE_DEFAULT_TIMEOUT')
    }
    
    if hasattr(cache, 'get_stats'):
        stats.update(cache.get_stats())
    
    return stats

def get(key: str) -> Optional[Any]:
    """Get a value from the cache."""
    if key not in _cache:
        return None
        
    if key in _cache_timeouts:
        if datetime.now() > _cache_timeouts[key]:
            del _cache[key]
            del _cache_timeouts[key]
            return None
            
    return _cache[key]

def set(key: str, value: Any, timeout: int = 300) -> None:
    """Set a value in the cache with timeout in seconds."""
    _cache[key] = value
    if timeout:
        _cache_timeouts[key] = datetime.now() + timedelta(seconds=timeout)

def delete(key: str) -> None:
    """Delete a value from the cache."""
    if key in _cache:
        del _cache[key]
    if key in _cache_timeouts:
        del _cache_timeouts[key]

def clear() -> None:
    """Clear the entire cache."""
    _cache.clear()
    _cache_timeouts.clear()

class Cache:
    """Cache decorator class."""
    
    def __init__(self, timeout: int = 300):
        """Initialize with timeout in seconds."""
        self.timeout = timeout
        
    def __call__(self, func: Callable) -> Callable:
        """Decorate a function with caching."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = get(key)
            if cached_value is not None:
                return cached_value
                
            # Call function and cache result
            result = func(*args, **kwargs)
            set(key, result, self.timeout)
            return result
            
        return wrapper
        
    def memoize(self, timeout: Optional[int] = None) -> Callable:
        """Memoize decorator with optional timeout override."""
        if timeout is not None:
            self.timeout = timeout
        return self 