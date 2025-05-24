"""DoppleGänger App Factory
===========================

Creates and configures the Flask application instance using the app factory pattern.
This allows flexible initialization across environments and contexts (CLI, gunicorn, testing, etc).
"""

import os
import platform
import logging
import time
from datetime import timedelta
from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory
from flask_login import LoginManager, current_user
from flask_cors import CORS
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_caching import Cache
from dotenv import load_dotenv
from flask_migrate import Migrate

from config import config as config_dict, Config
from extensions import init_extensions, db, login_manager
from config.cache import CacheConfig
from utils.image_paths import get_image_path, normalize_profile_image_path
from template_helpers import init_template_helpers
from utils.startup import run_startup_tasks
from models.user import User

# Import blueprints
from routes.main import main as main_blueprint
from routes.auth import auth as auth_blueprint
from routes.profile.view import profile_view
from routes.profile.edit import edit_profile_bp
from routes.profile.helpers import helpers as profile_helpers
from routes.face import face as face_blueprint
from routes.social import social as social_blueprint
from routes.search import search_bp

# Import blueprints
main = main_blueprint
auth = auth_blueprint
profile = profile_view
edit_profile = edit_profile_bp
profile_helpers = profile_helpers
face = face_blueprint
social = social_blueprint
search = search_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    config_name = os.environ.get('FLASK_ENV', 'development')
    config = config_dict.get(config_name, config_dict['default'])
    app.config.from_object(config)

    # === BEGIN Cascade Debug: Force Config Paths ===
    app.logger.info(f"[Cascade Debug] DB_PATH after from_object: {app.config.get('DB_PATH')}")
    app.logger.info(f"[Cascade Debug] INDEX_PATH after from_object: {app.config.get('INDEX_PATH')}")
    app.logger.info(f"[Cascade Debug] MAP_PATH after from_object: {app.config.get('MAP_PATH')}")

    correct_db_path = r'C:\Users\dumpy\Documents\Dopp\faces.db'
    correct_index_path = r'C:\Users\dumpy\Documents\Dopp\data\index\faces.index'
    correct_map_path = r'C:\Users\dumpy\Documents\Dopp\data\index\faces_filenames.pkl'

    app.config['DB_PATH'] = correct_db_path
    app.config['INDEX_PATH'] = correct_index_path
    app.config['MAP_PATH'] = correct_map_path

    app.logger.info(f"[Cascade Debug] DB_PATH after EXPLICIT override: {app.config.get('DB_PATH')}")
    app.logger.info(f"[Cascade Debug] INDEX_PATH after EXPLICIT override: {app.config.get('INDEX_PATH')}")
    app.logger.info(f"[Cascade Debug] MAP_PATH after EXPLICIT override: {app.config.get('MAP_PATH')}")
    # === END Cascade Debug: Force Config Paths ===

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

    # Configure Content Security Policy
    csp = {
        'default-src': ['self', 'unsafe-inline'],
        'style-src': ['self', 'unsafe-inline', 'unsafe-hashes', 'https://fonts.googleapis.com', 'http://localhost:5173'],
        'script-src': ['self', 'unsafe-inline', 'unsafe-eval'],
        'img-src': ['self', 'data:', 'https:', 'http:', 'http://localhost:5173'],
        'font-src': ['self', 'https://fonts.gstatic.com']
    }
    
    # Initialize Talisman with CSP
    Talisman(app, content_security_policy=csp)

    app = init_extensions(app)

    # Jinja helpers
    try:
        init_template_helpers(app)
    except Exception as e:
        import sys
        print(f"WARNING: Could not initialize template helpers: {e}", file=sys.stderr)

    # Session config
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=31)
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')

    # Cache configuration
    app.config['CACHE_TYPE'] = 'simple'  # Use simple cache for development
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    cache = Cache(app)
    app.cache = cache  # Make cache available through current_app

    # Utility injection
    @app.context_processor
    def inject_utilities():
        from flask_wtf.csrf import generate_csrf
        return dict(
            get_image_path=get_image_path,
            normalize_profile_image_path=normalize_profile_image_path,
            csrf_token=generate_csrf
        )

    # Logging
    LOG_TO_FILE = os.environ.get('DOPPLE_LOG_TO_FILE', '0') == '1'
    IS_WINDOWS = platform.system().lower().startswith('win')
    logger = logging.getLogger(__name__)
    LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(LOGS_DIR, exist_ok=True)
    handlers = [logging.StreamHandler()]
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    if not LOG_TO_FILE or IS_WINDOWS:
        logger.warning('File logging is disabled')

    # Login
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'
    
    csrf = CSRFProtect(app)
    
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=app.config.get('RATELIMIT_STORAGE_URL', 'memory://')
    )

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(int(user_id))

    # Register blueprints
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(profile_view, url_prefix='/profile')
    app.register_blueprint(face_blueprint, url_prefix='/face')
    app.register_blueprint(social_blueprint, url_prefix='/social')
    app.register_blueprint(search_bp)

    # Talisman security headers
    # Relax CSP for development to allow inline styles for React
    if app.config.get('ENV') == 'development' or app.config.get('DEBUG', False):
        talisman = Talisman(app, content_security_policy={
            'default-src': "'self'",
            'img-src': "'self' data: blob:",
            'style-src': "'self' 'unsafe-inline' https://fonts.googleapis.com http://localhost:5173 https://cdnjs.cloudflare.com",
            'script-src': "'self' 'unsafe-inline' https://cdnjs.cloudflare.com 'nonce-{}'".format(os.urandom(16).hex()),
            'font-src': "'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com",
            'connect-src': "'self' http://localhost:5173",
            'media-src': "'self'",
            'object-src': "'none'",
            'frame-src': "'self'",
            'base-uri': "'self'",
            # ... other directives ...
        })
    else:
        talisman = Talisman(app, content_security_policy={
            'default-src': "'self'",
            'img-src': "'self' data: blob:",
            'style-src': "'self' https://fonts.googleapis.com https://cdnjs.cloudflare.com",
            'script-src': "'self' https://cdnjs.cloudflare.com 'nonce-{}'".format(os.urandom(16).hex()),
            'font-src': "'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com",
            'connect-src': "'self'",
            'media-src': "'self'",
            'object-src': "'none'",
            'frame-src': "'self'",
            'base-uri': "'self'",
            'form-action': "'self'",
            'frame-ancestors': "'self'"
        }, force_https=False)

    # CORS
    trusted_origins = os.environ.get('TRUSTED_ORIGINS', '').split(',')
    if config_name == 'production' and '*' in trusted_origins:
        app.logger.error('Wildcard CORS origin not allowed in production')
        trusted_origins = [o for o in trusted_origins if o != '*']

    CORS(app,
         supports_credentials=True,
         resources={r"/*": {"origins": trusted_origins}},
         expose_headers=['Content-Range', 'X-Total-Count'])

    # Errors
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        app.logger.warning('CSRF failed', extra={'error': str(e)})
        return render_template('error.html', error="CSRF validation failed."), 400

    @app.errorhandler(429)
    def handle_ratelimit_error(e):
        app.logger.warning('Rate limit exceeded', extra={'error': str(e)})
        return render_template('error.html', error="Too many requests."), 429

    @app.errorhandler(500)
    def handle_internal_error(e):
        app.logger.error('500 error', extra={'error': str(e)})
        try:
            from models.sqlalchemy_models import db
            db.session.rollback()
        except Exception as db_exc:
            app.logger.error(f'DB rollback failed: {db_exc}')
        return render_template('500.html'), 500

    @app.errorhandler(404)
    def handle_not_found(e):
        app.logger.info('404 not found', extra={'path': request.path})
        return render_template('404.html'), 404

    @app.route('/health')
    def health():
        try:
            from models.sqlalchemy_models import db
            db.session.execute('SELECT 1')
            cache = app.extensions.get('cache_instance')
            cache.set('health_check', 'ok')
            cache.get('health_check')
            return {'status': 'ok', 'database': 'ok', 'cache': 'ok', 'version': app.config['VERSION']}, 200
        except Exception as e:
            app.logger.error(f'Health check failed: {str(e)}')
            return {'status': 'error', 'message': str(e)}, 500

    @app.before_request
    def start_timer():
        request._start_time = time.perf_counter()

    @app.after_request
    def log_request_time(response):
        if hasattr(request, '_start_time'):
            elapsed = time.perf_counter() - request._start_time
            app.logger.info(f"Request to {request.path} took {elapsed:.3f} sec")
        return response

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('search.search_page'))
        return redirect(url_for('auth.login'))

    # Register blueprints with unique names
    app.register_blueprint(main, name='main_bp')
    app.register_blueprint(auth, name='auth_bp')
    app.register_blueprint(profile, name='profile_bp')
    app.register_blueprint(edit_profile, name='edit_profile_bp')
    app.register_blueprint(profile_helpers, name='profile_helpers_bp')
    app.register_blueprint(face, name='face_bp')
    app.register_blueprint(social, name='social_bp')
    app.register_blueprint(search, name='search_bp')

    # Run startup tasks
    with app.app_context():
        run_startup_tasks(app)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)