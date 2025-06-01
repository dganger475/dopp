"""
Debug Utilities
=============

Provides debugging tools and utilities for development.
"""

import inspect
import logging
import os
import sys
from datetime import datetime
from flask import current_app, request, g
from functools import wraps

logger = logging.getLogger(__name__)

def debug_info():
    """Get debug information about the current application state."""
    info = {
        'environment': current_app.config.get('ENV'),
        'debug_mode': current_app.debug,
        'testing_mode': current_app.testing,
        'database_uri': current_app.config.get('SQLALCHEMY_DATABASE_URI'),
        'cache_type': current_app.config.get('CACHE_TYPE'),
        'session_type': current_app.config.get('SESSION_TYPE'),
        'upload_folder': current_app.config.get('UPLOAD_FOLDER'),
        'python_version': sys.version,
        'timestamp': datetime.now().isoformat()
    }
    
    # Add extension info
    info['extensions'] = {
        name: str(extension)
        for name, extension in current_app.extensions.items()
    }
    
    return info

def log_request_info(f):
    """Decorator to log detailed request information."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        # Log request details
        logger.debug(f"Request to {request.endpoint}:")
        logger.debug(f"Method: {request.method}")
        logger.debug(f"URL: {request.url}")
        logger.debug(f"Headers: {dict(request.headers)}")
        logger.debug(f"Args: {request.args}")
        logger.debug(f"Form: {request.form}")
        logger.debug(f"Files: {request.files}")
        
        # Track timing
        start = datetime.now()
        result = f(*args, **kwargs)
        duration = (datetime.now() - start).total_seconds()
        
        # Log response
        logger.debug(f"Response from {request.endpoint}:")
        logger.debug(f"Duration: {duration}s")
        logger.debug(f"Status: {result[1] if isinstance(result, tuple) else 200}")
        
        return result
    return wrapped

def debug_view(bp, url_prefix='/debug'):
    """Register debug views with a blueprint."""
    @bp.route(f'{url_prefix}/info')
    def view_debug_info():
        return debug_info()
    
    @bp.route(f'{url_prefix}/config')
    def view_config():
        return {k: v for k, v in current_app.config.items() 
                if not k.startswith('_') and isinstance(v, (str, int, float, bool, list, dict))}
    
    @bp.route(f'{url_prefix}/routes')
    def view_routes():
        routes = []
        for rule in current_app.url_map.iter_rules():
            routes.append({
                'endpoint': rule.endpoint,
                'methods': list(rule.methods),
                'path': str(rule)
            })
        return {'routes': routes}

def setup_debug_logging(app):
    """Configure detailed debug logging."""
    if app.debug:
        # Set up debug file handler
        debug_log = os.path.join(app.root_path, 'logs', 'debug.log')
        os.makedirs(os.path.dirname(debug_log), exist_ok=True)
        
        handler = logging.FileHandler(debug_log)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add handler to app logger
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.DEBUG) 