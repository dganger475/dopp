"""
CSRF protection utilities.
This module provides CSRF protection for the application using Flask-WTF.
"""

from flask import request
from flask_wtf.csrf import CSRFProtect


# Initialize CSRFProtect instance
csrf = CSRFProtect()

def init_csrf(app):
    """Initialize CSRF protection for the Flask app."""
    # Ensure CSRF is enabled. This is the default with Flask-WTF Forms,
    # but explicit is good. Set to False to globally disable (not recommended for production).
    app.config.setdefault('WTF_CSRF_ENABLED', True)
    
    # You can also set other CSRF related configs here if needed, e.g.:
    # app.config['WTF_CSRF_SECRET_KEY'] = 'a separate csrf secret key' 
    # app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour

    app.logger.info(f"CSRF WTF_CSRF_ENABLED before init: {app.config.get('WTF_CSRF_ENABLED')}")
    app.logger.info(f"CSRF WTF_CSRF_SECRET_KEY: {app.config.get('WTF_CSRF_SECRET_KEY')}")
    app.logger.info(f"CSRF SECRET_KEY (used by default if WTF_CSRF_SECRET_KEY is not set): {app.config.get('SECRET_KEY')}")
    app.logger.info(f"CSRF WTF_CSRF_TIME_LIMIT: {app.config.get('WTF_CSRF_TIME_LIMIT')}")
    csrf.init_app(app)
    app.logger.info("CSRF protection initialized and enabled after csrf.init_app.")
    app.logger.info(f"CSRF WTF_CSRF_ENABLED after init: {app.config.get('WTF_CSRF_ENABLED')}")

# Example of how to exempt specific views if needed (globally or per-blueprint/view)
# For example, if you have an API endpoint that doesn't use sessions/cookies
# and is protected by other means (e.g., API keys), you might exempt it.

# To exempt a specific view, you can use @csrf.exempt on that view function:
# from .routes.some_api_blueprint import some_api_route
# csrf.exempt(some_api_route)

# To exempt an entire blueprint:
# from .routes.api_blueprint import bp as api_bp
# csrf.exempt(api_bp)

# If you need more complex logic for exemption, you can use `before_request`
# @csrf.before_request
# def csrf_protect():
#     if request.path.startswith('/api/no-csrf'):
#         return # Skip CSRF check for this path
#     # For all other paths, CSRFProtect will handle it

