"""
Core Routes Module
=================

This module contains core routes that are essential to the application's functionality
but don't fit into other feature-specific blueprints. These include:
- Health check endpoint
- CSRF test endpoint
- Core utility routes
"""
from flask import Blueprint, current_app, jsonify, render_template, request, send_file
from flask_login import current_user, login_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import time
from .config import get_default_profile_image_path

core = Blueprint('core', __name__)

# === Health Check Endpoint ===
@core.route('/health')
def health():
    """Enhanced health check endpoint for uptime/monitoring."""
    try:
        from models.sqlalchemy_models import db
        db.session.execute('SELECT 1')
        cache = current_app.extensions.get('cache_instance')
        cache.set('health_check', 'ok')
        cache.get('health_check')
        return {
            'status': 'ok',
            'database': 'ok',
            'cache': 'ok',
            'version': current_app.config['VERSION']
        }, 200
    except Exception as e:
        current_app.logger.error(f'Health check failed: {str(e)}')
        return {'status': 'error', 'message': str(e)}, 500

# === CSRF Test Endpoint ===
@core.route("/csrf-test", methods=["GET", "POST"])
def csrf_test():
    """Test endpoint for CSRF protection."""
    if request.method == "POST":
        return "POST succeeded!"
    return render_template("csrf_test.html")

# === Default Image Serving ===
def send_default_image():
    """Helper function to send the default profile image."""
    return send_file(get_default_profile_image_path(), mimetype='image/png')

# === Request Timing for Bottleneck Detection ===
@core.before_request
def start_timer():
    """Start a timer before each request for performance monitoring."""
    request._start_time = time.perf_counter()

@core.after_request
def log_request_time(response):
    """Log the elapsed time for each request."""
    if hasattr(request, '_start_time'):
        elapsed = time.perf_counter() - request._start_time
        current_app.logger.info(f"Request to {request.path} took {elapsed:.3f} seconds")
    return response 