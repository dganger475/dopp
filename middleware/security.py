"""
Security Middleware
=================

Implements security headers and protections for the application.
"""

from functools import wraps
from flask import request, current_app, abort
import re
from utils.exceptions import AuthenticationError, AuthorizationError
from flask_caching import Cache

# Initialize cache
cache = Cache()

def security_headers(response):
    """Add security headers to response"""
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response

def validate_content_type(required_type):
    """Decorator to validate request content type"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.content_type != required_type:
                abort(415, f'Content type must be {required_type}')
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def sanitize_input(text):
    """Sanitize user input to prevent XSS"""
    if not text:
        return text
    # Remove potentially dangerous HTML tags and attributes
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.I | re.S)
    text = re.sub(r'<.*?javascript:.*?>', '', text, flags=re.I)
    text = re.sub(r'<.*?onclick=.*?>', '', text, flags=re.I)
    # Escape special characters
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    return text

def rate_limit(f):
    """Decorator to apply rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_app.config.get('RATE_LIMITING_ENABLED', False):
            return f(*args, **kwargs)
            
        # Get client IP
        ip = request.remote_addr
        
        # Check rate limit in Redis/cache
        key = f'rate_limit:{ip}:{request.endpoint}'
        
        try:
            current = cache.get(key) or 0
            
            if current >= current_app.config.get('RATE_LIMIT_MAX', 100):
                abort(429, 'Rate limit exceeded')
            
            # Increment counter
            cache.set(key, current + 1, timeout=60)  # Reset after 1 minute
            
        except Exception as e:
            current_app.logger.error(f"Rate limiting error: {str(e)}")
            # Continue if cache fails
            pass
            
        return f(*args, **kwargs)
    return decorated_function

def require_roles(*roles):
    """Decorator to check user roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                raise AuthenticationError('Authentication required')
            
            user_roles = set(current_user.roles)
            required_roles = set(roles)
            
            if not required_roles.issubset(user_roles):
                raise AuthorizationError('Insufficient permissions')
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def setup_security(app):
    """Configure security for the application"""
    
    @app.before_request
    def validate_request():
        # Check for required headers
        if app.config['ENV'] == 'production':
            if not request.is_secure:
                abort(400, 'HTTPS required')
        
        # Validate content length
        if request.content_length and request.content_length > app.config['MAX_CONTENT_LENGTH']:
            abort(413, 'Request too large')
    
    @app.after_request
    def after_request(response):
        return security_headers(response) 