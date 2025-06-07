"""DoppleGänger App Factory
===========================

Creates and configures the Flask application instance using the app factory pattern.
This allows flexible initialization across environments and contexts (CLI, gunicorn, testing, etc).
"""

# Monkey patch before any other imports
from gevent import monkey
monkey.patch_all()

import os
import platform
import logging
import time
from datetime import timedelta
import traceback
import socket

# Configure logging first
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Log environment information
logger.info(f"Python version: {platform.python_version()}")
logger.info(f"Platform: {platform.platform()}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Environment variables: {dict(os.environ)}")

# Import Flask and extensions
from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory, session, make_response
# Using custom CORS middleware
from utils.cors import setup_cors
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_caching import Cache
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate
from flask_compress import Compress
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import text

# Import template helpers
from template_helpers import init_template_helpers

# Import config after environment variables are loaded
from config.app_config import Config, get_config, get_settings
from config.cache import CacheConfig

# Import extensions (db will be initialized later)
from extensions import cache, limiter, session, talisman, login_manager, moment, db, init_extensions

# Import utility functions
from utils.startup import run_startup_tasks
from utils.image_paths import get_image_path, normalize_profile_image_path
from utils.image_urls import get_face_image_url, get_profile_image_url
from utils.db.storage import get_storage
from utils.files.utils import generate_face_filename, is_anonymized_face_filename, parse_face_id_from_filename
from utils.db.database import get_db, Base, engine

# Import models
from models.user import User

def register_blueprints(app):
    """Register Flask blueprints with app."""
    logger.info("Registering blueprints...")
    from routes.main import main
    from routes.auth import auth
    from routes.search import search
    from routes.profile.view import profile_view
    from routes.profile.edit import edit_profile
    from routes.profile.update import profile_update
    from routes.face import face
    from routes.social import social
    from routes.api import api
    from routes.api_users import api_users
    from routes.cors_proxy import cors_proxy
    from routes.test import test
    from routes.admin import admin
    from routes.face_upload import face_upload
    
    # Register blueprints
    app.register_blueprint(main, name='main')
    app.register_blueprint(auth, url_prefix='/auth', name='auth')
    app.register_blueprint(search, url_prefix='/search', name='search')
    app.register_blueprint(profile_view, url_prefix='/profile', name='profile')
    app.register_blueprint(edit_profile, url_prefix='/edit-profile', name='edit_profile')
    app.register_blueprint(profile_update, url_prefix='/profile', name='profile_update')
    app.register_blueprint(face, url_prefix='/face', name='face')
    app.register_blueprint(social, url_prefix='/social', name='social')
    app.register_blueprint(api, url_prefix='/api', name='api')
    app.register_blueprint(api_users, url_prefix='/api', name='api_users')
    app.register_blueprint(cors_proxy)
    app.register_blueprint(test)
    app.register_blueprint(admin, url_prefix='/admin', name='admin')
    app.register_blueprint(face_upload)
    logger.info("All blueprints registered successfully")

def test_db_connection(app):
    """Test database connection and log detailed information."""
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Testing database connection (attempt {attempt + 1}/{max_retries})...")
            with app.app_context():
                # Test basic connection
                logger.info("Attempting basic database connection...")
                result = db.session.execute(text('SELECT 1'))
                logger.info("Basic database connection successful")
                
                # Get database version
                logger.info("Getting database version...")
                version = db.session.execute(text('SELECT version()')).scalar()
                logger.info(f"Database version: {version}")
                
                # Get connection info
                logger.info("Getting connection info...")
                conn = db.engine.raw_connection()
                logger.info(f"Database connection info: {conn.info}")
                conn.close()
                
                # Test connection pool
                logger.info("Testing connection pool...")
                pool = db.engine.pool
                logger.info(f"Pool size: {pool.size()}")
                logger.info(f"Checked out connections: {pool.checkedin()}")
                logger.info(f"Available connections: {pool.checkedout()}")
                
                logger.info("Database connection test successful")
                return True
                
        except Exception as e:
            logger.error(f"Database connection test failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("All connection attempts failed")
                return False
    
    return False

def create_app(config_object=None):
    """Create and configure the Flask application."""
    logger.info("Creating Flask application...")
    app = Flask(__name__, static_folder='frontend/dist', static_url_path='')
    
    # Load configuration
    if config_object is None:
        config_object = get_config()
    app.config.from_object(config_object)
    logger.info("Configuration loaded")
    
    # Format database URL if needed
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('https://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('https://', 'postgresql://')
    
    # Add connection timeout settings with retry logic
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 5,
        'max_overflow': 10,
        'pool_timeout': 30,
        'pool_recycle': 1800,
        'pool_pre_ping': True,  # Enable connection health checks
        'connect_args': {
            'connect_timeout': 30,  # Increased timeout
            'application_name': 'dopple_app',
            'options': '-c statement_timeout=30000 -c idle_in_transaction_session_timeout=30000',  # 30 second timeout
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5
        }
    }
    
    # Log database configuration (without sensitive info)
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_url:
        # Mask password in logs
        masked_url = db_url.replace(db_url.split('@')[0], '***:***')
        logger.info(f"Database URL: {masked_url}")
    else:
        logger.error("No database URL configured!")
    
    # Initialize extensions first
    logger.info("Initializing extensions...")
    try:
        from extensions import init_extensions
        init_extensions(app)
        logger.info("Extensions initialized")
    except Exception as e:
        logger.error(f"Failed to initialize extensions: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    
    # Test database connection
    logger.info("Testing database connection...")
    if not test_db_connection(app):
        logger.error("Failed to connect to database. Application may not function correctly.")
        raise Exception("Database connection failed")
    
    # Setup CORS before registering blueprints
    logger.info("Setting up CORS...")
    app = setup_cors(app)
    
    # Setup CORS for local development and Vercel
    CORS(app, 
         supports_credentials=True, 
         origins=["http://localhost:5173", 
                 "http://127.0.0.1:5173", 
                 "http://localhost:5001", 
                 "http://127.0.0.1:5001", 
                 "https://doppleganger.us",
                 "https://dopple503.fly.dev"],
         allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "Cache-Control", "X-Csrf-Token", "X-CSRFToken"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
         expose_headers=["Content-Type", "Authorization"],
         max_age=86400,  # 24 hours
         send_wildcard=False)  # Don't send wildcard for credentials
    logger.info("CORS setup complete")
    
    # Configure Flask-Limiter
    logger.info("Configuring rate limiter...")
    app.config['RATELIMIT_STORAGE_URL'] = "file:///app/data/rate_limits"
    app.config['RATELIMIT_DEFAULT'] = ["200 per day", "50 per hour"]
    app.config['RATELIMIT_STRATEGY'] = "fixed-window"
    limiter.init_app(app)
    logger.info("Rate limiter configured")
    
    # Add health check endpoint
    @app.route('/health')
    def health_check():
        try:
            # Test database connection
            db.session.execute(text('SELECT 1'))
            return jsonify({
                "status": "healthy",
                "database": "connected"
            }), 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return jsonify({"status": "unhealthy", "error": str(e)}), 500
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        try:
            user = User.query.get(int(user_id))
            if user:
                # Ensure session is set
                session['user_id'] = user.id
            return user
        except Exception as e:
            app.logger.error(f"Error loading user: {str(e)}")
            return None
    
    # Register blueprints
    register_blueprints(app)
    
    # Initialize database tables
    logger.info("Initializing database tables...")
    with app.app_context():
        from extensions import db
        try:
            # Create tables if they don't exist
            db.create_all()
            logger.info("Successfully created/verified database tables")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    # Initialize template helpers
    logger.info("Initializing template helpers...")
    init_template_helpers(app)
    logger.info("Template helpers initialized")
    
    # Serve React App
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')
    
    logger.info("Flask application created successfully")
    return app

# Create the app instance for Gunicorn
logger.info("Creating application instance...")
app = create_app()
logger.info("Application instance created")

# Only run the app if this file is run directly
if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    
    # Check if port is available
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind((host, port))
        sock.close()
        logger.info(f"Port {port} is available")
    except socket.error as e:
        logger.error(f"Port {port} is not available: {e}")
        raise
    
    logger.info(f"Starting development server on {host}:{port}")
    app.run(host=host, port=port, threaded=True)