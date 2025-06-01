"""
Cache Configuration
=================

Configures caching with Redis support and fallback to simple cache.
"""

from flask_caching import Cache
from functools import wraps
from flask import request, current_app

# Initialize cache
cache = Cache()

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