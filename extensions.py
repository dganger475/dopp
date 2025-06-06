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
        
        # Configure Talisman for development
        logger.info("Configuring Talisman...")
        talisman.init_app(
            app,
            force_https=False,  # Don't force HTTPS in development
            strict_transport_security=False,  # Disable HSTS in development
            session_cookie_secure=False,  # Allow non-HTTPS cookies in development
            content_security_policy=None,  # Disable CSP in development
            feature_policy=None,  # Disable feature policy in development
        )
        
        logger.info("Initializing login manager...")
        login_manager.init_app(app)
        
        logger.info("Initializing moment...")
        moment.init_app(app)
        
        # Initialize limiter after app context is available
        logger.info("Initializing rate limiter...")
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
            from models.face import Face  # noqa: F401
            
            # Try to create tables with a timeout
            start_time = time.time()
            timeout = 30  # 30 seconds timeout
            
            try:
                logger.info("Creating database tables...")
                db.create_all()
                logger.info("Database tables created successfully")
            except Exception as e:
                logger.error(f"Error creating tables: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise
            
            # Run migrations with timeout
            try:
                logger.info("Running database migrations...")
                from flask_migrate import upgrade
                upgrade()
                logger.info("Database migrations completed successfully")
            except Exception as e:
                logger.error(f"Error running migrations: {str(e)}")
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
