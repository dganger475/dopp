"""
Cache Configuration

This module provides cache configuration for the DoppleGanger application.
Supports both in-memory and Redis-based caching.
"""
import os
from datetime import timedelta


class CacheConfig:
    """Cache configuration settings."""
    
    # Default cache type (redis or simple)
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'redis' if os.environ.get('REDIS_URL') else 'simple')
    
    # Redis configuration
    if CACHE_TYPE == 'redis':
        CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        CACHE_KEY_PREFIX = 'doppleganger:'
        CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
        CACHE_OPTIONS = {
            'socket_connect_timeout': 5,  # seconds
            'socket_timeout': 5,          # seconds
            'socket_keepalive': True
        }
    else:
        # Simple in-memory cache (for development)
        CACHE_TYPE = 'simple'
        CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes

    # Session configuration
    SESSION_TYPE = 'redis' if CACHE_TYPE == 'redis' else 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Rate limiting
    RATELIMIT_STORAGE_URL = CACHE_REDIS_URL if CACHE_TYPE == 'redis' else 'memory://'
    RATELIMIT_STRICT_ORDER = True
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_STORAGE_OPTIONS = CACHE_OPTIONS if CACHE_TYPE == 'redis' else {}
    
    # Face matching cache settings
    FACE_MATCH_CACHE_TIMEOUT = 3600  # 1 hour
    USER_PROFILE_CACHE_TIMEOUT = 300  # 5 minutes
    SEARCH_RESULTS_CACHE_TIMEOUT = 300  # 5 minutes
