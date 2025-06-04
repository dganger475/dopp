"""Configuration Management
=====================

This module handles application configuration with environment-specific settings.
"""

import os
from typing import Dict, Any
from datetime import timedelta

class Config:
    """Base configuration class."""
    
    # Application settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    DEBUG = False
    TESTING = False
    
    # Database settings
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/postgres')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.getenv('DATABASE_POOL_SIZE', '10')),
        'pool_timeout': int(os.getenv('DATABASE_POOL_TIMEOUT', '30')),
        'pool_recycle': int(os.getenv('DATABASE_POOL_RECYCLE', '1800')),
        'max_overflow': int(os.getenv('DATABASE_MAX_OVERFLOW', '5')),
        'echo': False
    }
    
    # Cache settings
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_THRESHOLD = int(os.getenv('CACHE_THRESHOLD', '1000'))
    
    # Rate limiting
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_STRATEGY = 'fixed-window'
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_HEADERS_RESET = True
    RATELIMIT_HEADERS_RETRY_AFTER = True
    RATELIMIT_HEADERS_REMAINING = True
    RATELIMIT_HEADERS_LIMIT = True
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
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
    
    # Face recognition
    FACE_RECOGNITION_MODEL = 'hog'  # or 'cnn' for GPU
    FACE_DETECTION_CONFIDENCE = 0.6
    FACE_MATCHING_THRESHOLD = 0.6
    
    # API configuration
    API_TITLE = 'Doppleganger API'
    OPENAPI_VERSION = '3.0.2'
    OPENAPI_URL_PREFIX = '/'
    OPENAPI_SWAGGER_UI_PATH = '/swagger-ui'
    OPENAPI_SWAGGER_UI_URL = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'
    
    # CORS
    CORS_ORIGINS = ['*']
    
    # Redis configuration (if using)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Email configuration (if using)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    # AWS configuration (if using)
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-west-2')
    S3_BUCKET = os.getenv('S3_BUCKET')
    
    # Google Cloud configuration (if using)
    GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    # Azure configuration (if using)
    AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    AZURE_STORAGE_CONTAINER = os.getenv('AZURE_STORAGE_CONTAINER')
    
    # Frontend configuration
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    
    # API Keys
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    STRIPE_API_KEY = os.getenv('STRIPE_API_KEY')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    # Feature flags
    ENABLE_FACE_RECOGNITION = True
    ENABLE_EMAIL_VERIFICATION = False
    ENABLE_SOCIAL_LOGIN = False
    ENABLE_PAYMENTS = False
    
    # Performance tuning
    SQLALCHEMY_POOL_SIZE = 20
    SQLALCHEMY_MAX_OVERFLOW = 5
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_POOL_RECYCLE = 1800
    
    # Debug mode
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    # Testing
    TESTING = False
    TEST_DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/test_db'

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
