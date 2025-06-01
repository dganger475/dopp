"""Configuration Management
=====================

This module handles application configuration with environment-specific settings.
"""

import os
from typing import Dict, Any

class Config:
    """Base configuration class."""
    
    # Application settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    DEBUG = False
    TESTING = False
    
    # Database settings
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///faces.db')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DATABASE_POOL_SIZE = int(os.getenv('DATABASE_POOL_SIZE', '10'))
    DATABASE_POOL_TIMEOUT = int(os.getenv('DATABASE_POOL_TIMEOUT', '30'))
    DATABASE_MAX_OVERFLOW = int(os.getenv('DATABASE_MAX_OVERFLOW', '5'))
    
    # Cache settings
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))
    CACHE_THRESHOLD = int(os.getenv('CACHE_THRESHOLD', '1000'))
    
    # Rate limiting
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '200 per day')
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # API settings
    API_RATE_LIMIT = os.getenv('API_RATE_LIMIT', '100 per minute')
    API_VERSION = '1.0'
    
    # Social features
    POSTS_PER_PAGE = int(os.getenv('POSTS_PER_PAGE', '20'))
    COMMENTS_PER_PAGE = int(os.getenv('COMMENTS_PER_PAGE', '50'))
    NOTIFICATIONS_PER_PAGE = int(os.getenv('NOTIFICATIONS_PER_PAGE', '20'))
    
    # Performance settings
    COMPRESS_MIMETYPES = [
        'text/html',
        'text/css',
        'text/xml',
        'application/json',
        'application/javascript'
    ]
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    CACHE_TYPE = 'simple'
    SESSION_COOKIE_SECURE = False
    
    # Development-specific settings
    DATABASE_POOL_SIZE = 5
    DATABASE_POOL_TIMEOUT = 10
    LOG_LEVEL = 'DEBUG'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    DATABASE_URL = 'sqlite:///:memory:'
    CACHE_TYPE = 'simple'
    SESSION_COOKIE_SECURE = False
    
    # Testing-specific settings
    DATABASE_POOL_SIZE = 1
    DATABASE_POOL_TIMEOUT = 5
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Production-specific settings
    CACHE_TYPE = 'filesystem'
    CACHE_DIR = os.getenv('CACHE_DIR', '/tmp/cache')
    LOG_LEVEL = 'WARNING'
    
    # Database settings for production
    DATABASE_URL = os.getenv('DATABASE_URL')  # Must be set in production
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_POOL_SIZE = int(os.getenv('SQLALCHEMY_POOL_SIZE', '20'))
    SQLALCHEMY_MAX_OVERFLOW = int(os.getenv('SQLALCHEMY_MAX_OVERFLOW', '10'))
    SQLALCHEMY_POOL_TIMEOUT = int(os.getenv('SQLALCHEMY_POOL_TIMEOUT', '30'))
    SQLALCHEMY_POOL_RECYCLE = int(os.getenv('SQLALCHEMY_POOL_RECYCLE', '1800'))
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Additional production settings
    PREFERRED_URL_SCHEME = 'https'
    SERVER_NAME = os.getenv('SERVER_NAME')
    APPLICATION_ROOT = os.getenv('APPLICATION_ROOT', '/')

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config() -> Config:
    """Get the appropriate configuration object based on environment."""
    env = os.getenv('FLASK_ENV', 'default')
    return config[env]

DEFAULT_PROFILE_IMAGE = 'images/default_profile.png'
