"""
Cache Utilities
==============

Provides centralized cache access and helper functions.
"""

import hashlib
import json
import logging
from functools import wraps

from flask import current_app

logger = logging.getLogger(__name__)


def cache_key(prefix, *args, **kwargs):
    """Generate a consistent cache key from function arguments.

    Args:
        prefix (str): A prefix for the cache key
        *args: Positional arguments to include in the key
        **kwargs: Keyword arguments to include in the key

    Returns:
        str: A string that can be used as a cache key
    """
    key_parts = [str(prefix)]

    # Add positional arguments to key
    for arg in args:
        key_parts.append(str(arg))

    # Add keyword arguments to key
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}:{v}")

    # Create a hash of the key to ensure it's a valid cache key
    key_str = ":".join(key_parts).encode("utf-8")
    return hashlib.md5(key_str).hexdigest()


def cached(timeout=300, key_prefix="cache_"):
    """Decorator to cache function results.

    Args:
        timeout (int): Cache timeout in seconds
        key_prefix (str): Prefix for cache keys

    Returns:
        function: Decorated function with caching
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Don't cache if cache is disabled
            if not current_app.config.get("CACHE_ENABLED", True):
                return f(*args, **kwargs)

            # Generate cache key
            # cache_key function handles string conversion of args/kwargs
            cache_key_str = cache_key(
                key_prefix + f.__name__,
                *args,  # Pass args directly
                **kwargs,  # Pass kwargs directly
            )

            # Try to get cached value
            # Assumes current_app.cache is a Flask-Caching compatible cache instance (e.g., SimpleCache, RedisCache)
            try:
                cached_value = current_app.cache.get(cache_key_str)
                if cached_value is not None:
                    logger.debug(f"Cache hit for {cache_key_str}")
                    return cached_value

                # Cache miss - call the function
                logger.debug(f"Cache miss for {cache_key_str}")
                result = f(*args, **kwargs)

                # Cache the result
                if result is not None:
                    current_app.cache.set(cache_key_str, result, timeout=timeout)

                return result

            except Exception as e:
                logger.error(f"Cache error in {f.__name__}: {str(e)}")
                # If there's a cache error, just call the function
                return f(*args, **kwargs)

        return decorated_function

    return decorator


def invalidate_cache(key_pattern):
    """Invalidate cache entries matching a pattern.

    Args:
        key_pattern (str): Pattern to match cache keys against

    Returns:
        int: Number of keys deleted
    """
    try:
        cache = current_app.cache
        # Note: delete_pattern is specific to certain cache backends like Redis.
        # For other backends (e.g., SimpleCache used by Flask-Caching in development),
        # this method might not be available or behave differently. Error handling is present.
        if hasattr(cache, "cache") and hasattr(
            cache.cache, "delete_pattern"
        ):  # Common for Redis via Flask-Caching
            return cache.cache.delete_pattern(key_pattern)
        elif hasattr(cache, "delete_matched"):  # Alternative some libraries might use
            return cache.delete_matched(key_pattern)
        else:
            logger.warning(
                f"Cache backend does not support a direct pattern deletion method like 'delete_pattern' or 'delete_matched'. Invalidation for '{key_pattern}' might be incomplete or not supported."
            )
        return 0
    except Exception as e:
        logger.error(f"Error invalidating cache pattern {key_pattern}: {str(e)}")
        return 0


def clear_all_caches():
    """Clear all cached data.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cache = current_app.cache
        if hasattr(cache, "clear"):
            return cache.clear()
        return False
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return False


def get_cache_value(key, default=None):
    """Get a value from the cache."""
    try:
        return current_app.extensions['cache'].get(key, default)
    except Exception as e:
        logger.error(f"Cache get error for key {key}: {str(e)}")
        return default


def set_cache_value(key, value, timeout=None):
    """Set a value in the cache."""
    try:
        current_app.extensions['cache'].set(key, value, timeout=timeout)
    except Exception as e:
        logger.error(f"Cache set error for key {key}: {str(e)}")


def delete_cache_value(key):
    """Delete a value from the cache."""
    try:
        current_app.extensions['cache'].delete(key)
    except Exception as e:
        logger.error(f"Cache delete error for key {key}: {str(e)}")


def increment_cache_value(key, timeout=None):
    """Increment a value in the cache."""
    try:
        value = get_cache_value(key, 0)
        value += 1
        set_cache_value(key, value, timeout=timeout)
        return value
    except Exception as e:
        logger.error(f"Cache increment error for key {key}: {str(e)}")
        return 0
