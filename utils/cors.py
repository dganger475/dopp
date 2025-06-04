"""
CORS Handler Module
==================

Comprehensive CORS handling for Flask applications with special
attention to preflight requests and authentication routes.
"""
from flask import request, make_response, current_app

def setup_cors(app):
    """
    Configure comprehensive CORS handling for the Flask app.
    
    This sets up both before_request and after_request handlers to ensure
    OPTIONS requests are properly handled without authentication requirements
    and all responses have appropriate CORS headers.
    """
    # Explicitly define allowed origins for development and beta testing
    allowed_origins = [
        'http://localhost:5173',  # Vite dev server
        'http://127.0.0.1:5173',
        'http://localhost:3000',  # React dev server
        'http://127.0.0.1:3000',
        'http://localhost:8080',  # Another common dev port
        'http://127.0.0.1:8080',
        # Production domain
        'https://doppleganger.us',
        # Allow ngrok URLs for beta testing
        'https://*.ngrok.io',
        'https://*.ngrok-free.app'
    ]
    
    # Function to check if origin matches allowed origins including wildcards
    def is_allowed_origin(origin, allowed_origins):
        if not origin:
            return False
            
        # Check exact matches first
        if origin in allowed_origins:
            return True
            
        # Check wildcard matches
        for allowed in allowed_origins:
            if allowed.startswith('https://*.') and origin.startswith('https://'):
                # Extract domain suffix after the wildcard
                suffix = allowed.replace('https://*.', '')
                if origin.endswith(suffix):
                    return True
        return False
        
    @app.before_request
    def handle_preflight():
        # Skip authentication for OPTIONS requests
        if request.method == 'OPTIONS':
            origin = request.headers.get('Origin', '')
            # Check if origin is in allowed list or if we're in development mode
            if is_allowed_origin(origin, allowed_origins) or app.config.get('ENV') == 'development':
                headers = {
                    'Access-Control-Allow-Origin': origin,
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS, PATCH',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Cache-Control, X-Csrf-Token, X-CSRFToken',
                    'Access-Control-Allow-Credentials': 'true',
                    'Access-Control-Max-Age': '86400',  # 24 hours
                    'Content-Type': 'text/plain'
                }
                # Return an empty 200 response with CORS headers
                return make_response('', 200, headers)
    
    # After request handler for all responses
    @app.after_request
    def add_cors_headers(response):
        # Get the origin from the request
        origin = request.headers.get('Origin')
        
        # Always add CORS headers, regardless of response status
        # This ensures CORS headers are present even for error responses
        
        # If origin is in allowed list (including wildcard matches), set the header
        if is_allowed_origin(origin, allowed_origins):
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        # If there's a specific origin and we're in development, use it
        elif origin and app.config.get('ENV') == 'development':
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        # Otherwise allow all origins (only for development)
        elif app.config.get('ENV') == 'development':
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            
        # Log CORS headers for debugging
        if app.config.get('DEBUG', False):
            app.logger.debug(f"CORS headers for {request.path} (status {response.status_code}): Origin={origin}, ACAO={response.headers.get('Access-Control-Allow-Origin')}")
            
        # Add standard CORS headers to all responses
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Cache-Control, X-Csrf-Token, X-CSRFToken'
        
        # Add Vary header for proper caching
        response.headers['Vary'] = 'Origin'
        
        return response
        
    # Return the app to fix the app = setup_cors(app) issue
    return app
