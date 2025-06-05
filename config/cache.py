"""
Cache Configuration

This module provides cache configuration for the DoppleGanger application.
Supports both in-memory and Redis-based caching.
"""
import os
from datetime import timedelta


class CacheConfig:
    """Cache configuration settings."""
    
    # Cache type (SimpleCache, RedisCache, etc.)
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'SimpleCache')
    
    # Cache timeout in seconds
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))
    
    # Cache threshold (max number of items)
    CACHE_THRESHOLD = int(os.getenv('CACHE_THRESHOLD', '1000'))
    
    # Redis specific settings (if using RedisCache)
    CACHE_REDIS_HOST = os.getenv('CACHE_REDIS_HOST', 'localhost')
    CACHE_REDIS_PORT = int(os.getenv('CACHE_REDIS_PORT', '6379'))
    CACHE_REDIS_PASSWORD = os.getenv('CACHE_REDIS_PASSWORD')
    CACHE_REDIS_DB = int(os.getenv('CACHE_REDIS_DB', '0'))
    
    # Filesystem cache settings (if using FileSystemCache)
    CACHE_DIR = os.getenv('CACHE_DIR', '/tmp/cache')
    
    # Memcached settings (if using MemcachedCache)
    CACHE_MEMCACHED_SERVERS = os.getenv('CACHE_MEMCACHED_SERVERS', 'localhost:11211')
    
    # Cache key prefix
    CACHE_KEY_PREFIX = os.getenv('CACHE_KEY_PREFIX', 'dopple_')
    
    # Cache options
    CACHE_OPTIONS = {
        'CACHE_DEFAULT_TIMEOUT': CACHE_DEFAULT_TIMEOUT,
        'CACHE_THRESHOLD': CACHE_THRESHOLD,
        'CACHE_KEY_PREFIX': CACHE_KEY_PREFIX
    }
    
    # Add Redis options if using Redis
    if CACHE_TYPE == 'RedisCache':
        CACHE_OPTIONS.update({
            'CACHE_REDIS_HOST': CACHE_REDIS_HOST,
            'CACHE_REDIS_PORT': CACHE_REDIS_PORT,
            'CACHE_REDIS_PASSWORD': CACHE_REDIS_PASSWORD,
            'CACHE_REDIS_DB': CACHE_REDIS_DB
        })
    
    # Add Filesystem options if using FileSystem
    elif CACHE_TYPE == 'FileSystemCache':
        CACHE_OPTIONS.update({
            'CACHE_DIR': CACHE_DIR
        })
    
    # Add Memcached options if using Memcached
    elif CACHE_TYPE == 'MemcachedCache':
        CACHE_OPTIONS.update({
            'CACHE_MEMCACHED_SERVERS': CACHE_MEMCACHED_SERVERS
        })

    # Default cache type (redis or simple)
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'redis' if os.environ.get('REDIS_URL') else 'simple')
    
    # Redis configuration
    if CACHE_TYPE == 'redis':
        CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
        CACHE_OPTIONS = {
            'socket_connect_timeout': 5,  # seconds
            'socket_timeout': 5,          # seconds
            'socket_keepalive': True,
            'retry_on_timeout': True,
            'max_connections': 50
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
