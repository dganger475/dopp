"""
Central place to initialize Flask extensions for the DoppleGänger app.
This module uses a factory pattern for extension initialization.
"""
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session
from flask_talisman import Talisman
from flask_login import LoginManager
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import session, current_app
import logging
import time
import traceback
import os

logger = logging.getLogger(__name__)

# Create extension instances without initializing them
cache = Cache()

def get_limiter_key():
    """Get a unique key for rate limiting based on user session."""
    try:
        if 'user_id' in session:
            return f"user_{session['user_id']}"
    except Exception as e:
        current_app.logger.error(f"Error getting session user_id: {e}")
    return get_remote_address()

limiter = Limiter(key_func=get_limiter_key)
session_store = Session()
talisman = Talisman()
login_manager = LoginManager()
moment = Moment()
db = SQLAlchemy()
migrate = Migrate()

def init_extensions(app):
    """Initialize Flask extensions with the given app instance."""
    try:
        # Initialize extensions that don't depend on others
        logger.info("Initializing cache...")
        cache.init_app(app)
        
        # Configure session
        logger.info("Configuring session...")
        app.config['SESSION_TYPE'] = app.config.get('SESSION_TYPE', 'filesystem')
        app.config['SESSION_FILE_DIR'] = app.config.get('SESSION_FILE_DIR', 'flask_session')
        app.config['SESSION_PERMANENT'] = app.config.get('SESSION_PERMANENT', True)
        app.config['PERMANENT_SESSION_LIFETIME'] = app.config.get('PERMANENT_SESSION_LIFETIME', 3600)
        app.config['SESSION_COOKIE_SECURE'] = app.config.get('SESSION_COOKIE_SECURE', True)
        app.config['SESSION_COOKIE_HTTPONLY'] = app.config.get('SESSION_COOKIE_HTTPONLY', True)
        app.config['SESSION_COOKIE_SAMESITE'] = app.config.get('SESSION_COOKIE_SAMESITE', 'Lax')
        session_store.init_app(app)
        
        # Configure Talisman for production
        logger.info("Configuring Talisman...")
        is_production = app.config.get('FLASK_ENV') == 'production'
        talisman.init_app(
            app,
            force_https=is_production,  # Force HTTPS in production
            content_security_policy={
                'default-src': "'self'",
                'img-src': "'self' data: https:",
                'script-src': "'self' 'unsafe-inline' 'unsafe-eval'",
                'style-src': "'self' 'unsafe-inline'",
                'connect-src': "'self' https: wss:",
                'font-src': "'self' data: https:",
                'frame-src': "'self'",
                'media-src': "'self' https:",
                'object-src': "'none'",
                'base-uri': "'self'",
                'form-action': "'self'",
                'frame-ancestors': "'none'",
                'upgrade-insecure-requests': '1' if is_production else None
            },
            session_cookie_secure=is_production,  # Secure cookies in production
            strict_transport_security=is_production,  # HSTS in production
            feature_policy={
                'geolocation': "'none'",
                'midi': "'none'",
                'sync-xhr': "'self'",
                'microphone': "'none'",
                'camera': "'none'",
                'magnetometer': "'none'",
                'gyroscope': "'none'",
                'speaker': "'self'",
                'fullscreen': "'self'",
                'payment': "'none'",
                'usb': "'none'"
            }
        )
        
        logger.info("Initializing login manager...")
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'
        login_manager.login_message_category = 'info'
        
        logger.info("Initializing moment...")
        moment.init_app(app)
        
        # Initialize limiter after app context is available
        logger.info("Initializing rate limiter...")
        is_production = app.config.get('FLASK_ENV') == 'production'
        
        if is_production:
            # Use Redis in production
            app.config['RATELIMIT_STORAGE_URL'] = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            app.config['RATELIMIT_STORAGE_OPTIONS'] = {
                'socket_timeout': 5,
                'socket_connect_timeout': 5,
                'retry_on_timeout': True
            }
        else:
            # Use memory storage in development
            app.config['RATELIMIT_STORAGE_URL'] = 'memory://'
        
        limiter.init_app(app)
        
        # Initialize SQLAlchemy and Migrate with PostgreSQL-specific settings
        logger.info("Initializing SQLAlchemy...")
        db.init_app(app)
        
        logger.info("Initializing migrations...")
        migrate.init_app(app, db)
        
        # Import models after db is initialized to prevent circular imports
        logger.info("Setting up database tables...")
        with app.app_context():
            # This will create tables if they don't exist
            logger.info("Importing models...")
            from models.user import User  # noqa: F401
            from models.social.post import Post, PostImage, PostReaction  # noqa: F401
            from models.social.comment import Comment  # noqa: F401
            from models.social.like import Like  # noqa: F401
            
            # Try to create tables with a timeout
            start_time = time.time()
            timeout = 30  # 30 seconds timeout
            
            try:
                logger.info("Creating database tables...")
                # Create all tables using metadata
                db.create_all()
                logger.info("Database tables created successfully")
                
                # Skip migrations for now since we're using create_all()
                logger.info("Skipping migrations as tables are created with create_all()")
                
            except Exception as e:
                logger.error(f"Error during database setup: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise
            
            if time.time() - start_time > timeout:
                raise TimeoutError("Database initialization timed out")
        
        logger.info("All extensions initialized successfully")
        return app
        
    except Exception as e:
        logger.error(f"Failed to initialize extensions: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
