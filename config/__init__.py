# Configuration package
import os
from datetime import timedelta


class Config:
    """Base configuration class."""
    # Use environment variable for secret key; fallback is insecure and for development only
    # Fallback key is insecure and for development only!
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-insecure-key')
    
    # Session type for Flask-Session
    SESSION_TYPE = 'filesystem'
    
    # Session file directory
    SESSION_FILE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance', 'flask_session')
    
    # Data directories
    DATA_ROOT = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'data')
    DB_DIR = os.path.join(DATA_ROOT, 'db')
    INDEX_DIR = os.path.join(DATA_ROOT, 'index')
    
    # Ensure data directories exist
    os.makedirs(DB_DIR, exist_ok=True)
    os.makedirs(INDEX_DIR, exist_ok=True)
    
    # Database paths
    DB_PATH = os.environ.get('DB_PATH', os.path.join(DB_DIR, 'faces.db'))
    
    # SQLAlchemy config
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.abspath(DB_PATH)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Face recognition paths
    INDEX_PATH = os.environ.get('INDEX_PATH', os.path.join(INDEX_DIR, 'faces.index'))
    MAP_PATH = os.environ.get('MAP_PATH', os.path.join(INDEX_DIR, 'faces_filenames.pkl'))
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # Static directories
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'static/uploads')
    EXTRACTED_FACES = os.environ.get('EXTRACTED_FACES', 'static/extracted_faces')
    PROFILE_PICS = os.environ.get('PROFILE_PICS', 'static/profile_pics')
    COVER_PICS = os.environ.get('COVER_PICS', 'static/covers')
    DEFAULT_PROFILE_IMAGE = os.environ.get('DEFAULT_PROFILE_IMAGE', 'static/default_profile.png')
    DEFAULT_COVER_IMAGE = os.environ.get('DEFAULT_COVER_IMAGE', 'static/default_cover.jpg')
    
    # Session config
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', '0') == '1'
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', '1') == '1'
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    
    # Feature toggles
    ENABLE_EMAIL_VERIFICATION = os.environ.get('ENABLE_EMAIL_VERIFICATION', '0') == '1'
    ENABLE_PASSWORD_RESET = os.environ.get('ENABLE_PASSWORD_RESET', '0') == '1'
    
    @staticmethod
    def init_app(app):
        print("--- PRINT: Attempting to enter Config.init_app (from config/__init__.py) ---")
        app.logger.warning("--- LOG: Entering Config.init_app (from config/__init__.py) ---")
        """Initialize app with this configuration."""
        # Create necessary directories
        app.logger.warning(f"--- LOG: Config.UPLOAD_FOLDER: {Config.UPLOAD_FOLDER} ---")
        os.makedirs(os.path.join(app.root_path, Config.UPLOAD_FOLDER), exist_ok=True)
        app.logger.warning(f"--- LOG: Config.EXTRACTED_FACES: {Config.EXTRACTED_FACES} ---")
        os.makedirs(os.path.join(app.root_path, Config.EXTRACTED_FACES), exist_ok=True)
        app.logger.warning(f"--- LOG: Config.PROFILE_PICS: {Config.PROFILE_PICS} ---")
        os.makedirs(os.path.join(app.root_path, Config.PROFILE_PICS), exist_ok=True)
        app.logger.warning(f"--- LOG: Config.COVER_PICS: {Config.COVER_PICS} ---")
        cover_pics_path = os.path.join(app.root_path, Config.COVER_PICS)
        app.logger.warning(f"--- LOG: Attempting to create cover_pics_path: {cover_pics_path} ---")
        os.makedirs(cover_pics_path, exist_ok=True)
        app.logger.warning(f"--- LOG: Directory {cover_pics_path} exists: {os.path.exists(cover_pics_path)} ---")


class DevelopmentConfig(Config):
    """Development environment configuration."""
    # Only enable debug mode if FLASK_DEBUG or DOPPLE_DEBUG env var is set
    DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
    TESTING = False
    
    # Additional development settings
    TEMPLATES_AUTO_RELOAD = True


class TestingConfig(Config):
    """Testing environment configuration."""
    DEBUG = False
    TESTING = True
    
    # Use in-memory database for tests
    DB_PATH = ":memory:"
    
    # Temp directories for testing
    UPLOAD_FOLDER = os.path.join("static", "test_uploads")
    EXTRACTED_FACES = os.path.join("static", "test_extracted_faces")
    
    # Additional testing settings
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    TESTING = False
    
    # These should be set through environment variables in production
    # Use environment variable for secret key; do not hardcode in production
    # Fallback key is insecure and for development only!
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'prod-insecure-key'
    
    # Enable security features in production
    ENABLE_EMAIL_VERIFICATION = True
    ENABLE_PASSWORD_RESET = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


# Import development config
from .development import DevelopmentConfig

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Retrieve configuration by name.
    
    Args:
        config_name (str, optional): Name of the configuration to retrieve. 
                                   Defaults to 'default'.
    
    Returns:
        Config: The configuration class.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    config_obj = config.get(config_name.lower(), config['default'])
    
    # Initialize the config object if it's a class
    if isinstance(config_obj, type):
        config_obj = config_obj()
    
    return config_obj
