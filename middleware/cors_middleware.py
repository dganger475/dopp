"""
CORS Middleware for DoppleGänger
================================

Custom CORS middleware to ensure proper headers are added to all responses.
This helps solve cross-origin issues between the frontend and backend.
"""

from flask import request, make_response, current_app
import logging

class CORSMiddleware:
    """Middleware to add CORS headers to all responses."""
    
    def __init__(self, app):
        """Initialize the middleware with a Flask app."""
        self.app = app
        self.init_app(app)
        
    def init_app(self, app):
        """Register the middleware with a Flask app."""
        # Ensure this middleware runs before any other request handlers
        app.before_request(self.handle_preflight_request)
        # Ensure this middleware runs after all response handlers
        app.after_request(self.add_cors_headers)
        
    def handle_preflight_request(self):
        """Handle OPTIONS requests before they reach route handlers that might redirect."""
        if request.method == 'OPTIONS':
            # ALL OPTIONS requests should be handled here to prevent redirects
            # especially for authentication-related endpoints
            
            # Log the preflight request
            current_app.logger.debug(f"CORS Preflight Request: Path={request.path}, Origin={request.headers.get('Origin')}")
            
            # Create a direct response to the preflight request
            response = make_response()
            response.status_code = 200  # Ensure OK status
            
            # Set required CORS headers
            response.headers['Access-Control-Allow-Origin'] = '*'
            
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            
            # Always include these headers for all OPTIONS requests
            allowed_headers = [
                'Content-Type', 'Authorization', 'X-Requested-With', 
                'Accept', 'Origin', 'Cache-Control', 'cache-control', 'X-Csrf-Token', 'X-CSRFToken'
            ]
            
            # Handle requested headers
            requested_headers = request.headers.get('Access-Control-Request-Headers')
            if requested_headers:
                # Combine requested headers with our allowed headers
                all_headers = set(allowed_headers + [h.strip() for h in requested_headers.split(',')])
                response.headers['Access-Control-Allow-Headers'] = ','.join(all_headers)
            else:
                response.headers['Access-Control-Allow-Headers'] = ','.join(allowed_headers)
            
            # Always allow all common methods
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
            
            # Cache preflight response for 1 day
            response.headers['Access-Control-Max-Age'] = '86400'  # 1 day
            
            # Add Vary header for proper caching
            response.headers['Vary'] = 'Origin'
            
            # Log the preflight response
            current_app.logger.debug(f"CORS Preflight Response Headers: {dict(response.headers)}")
            
            # Return the response immediately, bypassing any route logic
            return response
            
        # For non-OPTIONS requests, continue to the route handler
        return None
        
    def add_cors_headers(self, response):
        """Add CORS headers to responses from route handlers."""
        # Skip if this is an OPTIONS request that was already handled
        if request.method == 'OPTIONS' and 'Access-Control-Allow-Origin' in response.headers:
            return response
            
        # Add CORS headers to all other responses
        origin = request.headers.get('Origin')
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            # Allow all origins for beta testing
            response.headers['Access-Control-Allow-Origin'] = '*'
        
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        allowed_headers = [
            'Content-Type', 'Authorization', 'X-Requested-With', 
            'Accept', 'Origin', 'Cache-Control', 'cache-control', 'X-Csrf-Token', 'X-CSRFToken'
        ]
        response.headers['Access-Control-Allow-Headers'] = ','.join(allowed_headers)
        
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
        
        # Add Vary header for proper caching
        response.headers['Vary'] = 'Origin'
        
        # Log response headers for debugging
        if current_app.config.get('DEBUG', False):
            current_app.logger.debug(f"CORS Response: Path={request.path}, Status={response.status_code}, Origin={origin}, Headers={dict(response.headers)}")
        
        return response

def configure_cors(app):
    """Configure CORS for the Flask application."""
    CORSMiddleware(app)
    return app
