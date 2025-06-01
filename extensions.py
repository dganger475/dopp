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
    # Initialize extensions that don't depend on others
    cache.init_app(app)
    
    # Configure session
    app.config['SESSION_TYPE'] = app.config.get('SESSION_TYPE', 'filesystem')
    app.config['SESSION_FILE_DIR'] = app.config.get('SESSION_FILE_DIR', 'flask_session')
    app.config['SESSION_PERMANENT'] = app.config.get('SESSION_PERMANENT', True)
    app.config['PERMANENT_SESSION_LIFETIME'] = app.config.get('PERMANENT_SESSION_LIFETIME', 3600)
    app.config['SESSION_COOKIE_SECURE'] = app.config.get('SESSION_COOKIE_SECURE', True)
    app.config['SESSION_COOKIE_HTTPONLY'] = app.config.get('SESSION_COOKIE_HTTPONLY', True)
    app.config['SESSION_COOKIE_SAMESITE'] = app.config.get('SESSION_COOKIE_SAMESITE', 'Lax')
    session_store.init_app(app)
    
    talisman.init_app(app)
    login_manager.init_app(app)
    moment.init_app(app)
    
    # Initialize limiter after app context is available
    limiter.init_app(app)
    
    # Initialize SQLAlchemy and Migrate
    print("Initializing SQLAlchemy with app:", app)
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Import models after db is initialized to prevent circular imports
    with app.app_context():
        # This will create tables if they don't exist
        from models.user import User  # noqa: F401
        db.create_all()
        
        # Initialize the database connection pool
        from utils.db.database import init_app as init_db
        init_db(app)
    
    return app
