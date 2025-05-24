"""
Application Configuration
=======================

Handles all configuration settings with environment-specific values.
"""
import os
from datetime import timedelta

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

class BaseConfig:
    """Base configuration class"""
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    PROFILE_PICS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'profile_pics')
    DEFAULT_PROFILE_IMAGE = 'images/default_profile.png'  # Path relative to static folder
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_MAX_OVERFLOW = 20
    
    # Cache
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Rate Limiting
    RATELIMIT_DEFAULT = "200 per day;50 per hour;10 per minute"
    RATELIMIT_STORAGE_URL = "memory://"
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE = 'app.log'
    
    # Password Policy
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_NUMBERS = True
    PASSWORD_REQUIRE_SPECIAL = True
    
    # API
    API_VERSION = 'v1'
    API_DEFAULT_PAGE_SIZE = 20
    API_MAX_PAGE_SIZE = 100

class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(_PROJECT_ROOT, 'faces.db')
    SESSION_COOKIE_SECURE = False

    # --- Paths for FAISS and face encodings DB ---
    # Assuming config.py is in the project root (C:\Users\dumpy\Documents\Dopp)
    # _PROJECT_ROOT is now defined at module level
    DB_PATH = r'C:\Users\dumpy\Documents\Dopp\faces.db' # Points to faces.db at the project root
    
    _FAISS_INDEX_DIR = os.path.join(_PROJECT_ROOT, 'data', 'index')
    INDEX_PATH = os.path.join(_FAISS_INDEX_DIR, 'faces.index')
    MAP_PATH = os.path.join(_FAISS_INDEX_DIR, 'faces_filenames.pkl')
    
    # Ensure the FAISS index directory exists (optional, can be handled in app factory)
    # os.makedirs(_FAISS_INDEX_DIR, exist_ok=True)

class TestingConfig(BaseConfig):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False

class ProductionConfig(BaseConfig):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL')
    LOG_LEVEL = 'ERROR'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 