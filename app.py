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
import sqlite3

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

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
from utils.db.database import get_users_db_connection
from flask_compress import Compress
from flask_sqlalchemy import SQLAlchemy

# Import template helpers
from template_helpers import init_template_helpers

# Import config after environment variables are loaded
from config import config as config_dict, Config
from config.cache import CacheConfig

# Import extensions (db will be initialized later)
from extensions import cache, limiter, session, talisman, login_manager, moment, db, init_extensions

# Import utility functions
from utils.startup import run_startup_tasks
from utils.image_paths import get_image_path, normalize_profile_image_path
from utils.image_urls import get_face_image_url, get_profile_image_url
from utils.db.storage import get_storage
from utils.files.utils import generate_face_filename, is_anonymized_face_filename, parse_face_id_from_filename

# Import models
from models.user import User

def register_blueprints(app):
    """Register Flask blueprints with app."""
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
    
    # Make blueprints available if needed
    app.blueprints = {
        'main': main,
        'auth': auth,
        'profile': profile_view,
        'edit_profile': edit_profile,
        'profile_update': profile_update,
        'face': face,
        'social': social,
        'search': search,
        'api': api,
        'api_users': api_users,
        'admin': admin
    }

def create_app(config_class=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder='frontend/dist', static_url_path='')
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    if config_class == 'testing':
        from config import TestingConfig
        app.config.from_object(TestingConfig)
    else:
        # your normal config loading
        from config import Config
        from config.cache import CacheConfig
        app.config.from_object(Config)
        app.config.from_object(CacheConfig)
    
    # Log database configuration
    logger.info(f"Database URL: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
    
    # Initialize extensions first
    from extensions import init_extensions
    init_extensions(app)
    
    # Setup CORS before registering blueprints
    app = setup_cors(app)
    
    # Setup CORS for local development and Vercel
    from flask_cors import CORS
    CORS(app, 
         supports_credentials=True, 
         origins=["http://localhost:5173", 
                 "http://127.0.0.1:5173", 
                 "http://localhost:5001", 
                 "http://127.0.0.1:5001", 
                 "https://doppleganger.us"],
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
         expose_headers=["Content-Type", "Authorization"],
         max_age=86400)  # 24 hours
    
    # Add health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({"status": "healthy"}), 200
    
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
    with app.app_context():
        from extensions import db
        try:
            # Create tables if they don't exist
            db.create_all()
            logger.info("Successfully created/verified database tables")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    # Initialize template helpers
    init_template_helpers(app)
    
    # Serve React App
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')
    
    return app

# Create the app instance for Gunicorn
app = create_app()

# Only run the app if this file is run directly
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)