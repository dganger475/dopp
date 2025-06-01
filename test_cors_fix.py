"""
CORS Test and Fix for Doppleganger App
======================================

This script tests and implements a solution for the CORS issue with the /auth/current_user endpoint.
"""

from flask import Flask, request, jsonify, session
from flask_login import LoginManager, login_required, current_user
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a minimal test application
app = Flask(__name__)
app.secret_key = 'test_secret_key'

# Configure login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Critical: Explicitly ensure OPTIONS requests are exempt from authentication
login_manager.exempt_methods = ('OPTIONS',)

@login_manager.user_loader
def load_user(user_id):
    # Return None for testing
    return None

class DirectCORSMiddleware:
    """Simple CORS middleware that handles OPTIONS requests before any routing logic."""
    
    def __init__(self, app):
        self.app = app
        self.app.before_request(self.handle_cors)
    
    def handle_cors(self):
        """Handle CORS preflight requests."""
        print(f"[CORS] {request.method} {request.path}")
        # For all OPTIONS requests, return immediate response with CORS headers
        if request.method == 'OPTIONS':
            logger.debug(f"Handling OPTIONS request to {request.path}")
            print(f"[CORS] Handling OPTIONS request to {request.path}")
            response = jsonify({"status": "preflight_ok", "path": request.path})
            response.status_code = 200
            # Add CORS headers
            origin = request.headers.get('Origin')
            if origin:
                logger.debug(f"Setting Access-Control-Allow-Origin: {origin}")
                print(f"[CORS] Setting Access-Control-Allow-Origin: {origin}")
                response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Cache-Control, cache-control, X-Csrf-Token, X-CSRFToken'
            response.headers['Access-Control-Max-Age'] = '86400'  # 24 hours
            logger.debug(f"CORS headers set: {dict(response.headers)}")
            print(f"[CORS] CORS headers set: {dict(response.headers)}")
            return response
        return None

# Apply CORS middleware
cors = DirectCORSMiddleware(app)

# Route that mimics the current_user endpoint
@app.route('/auth/current_user', methods=['GET', 'OPTIONS'])
def test_current_user():
    """Test endpoint that behaves like the current_user endpoint."""
    logger.debug(f"Received {request.method} request to /auth/current_user")
    
    # Already handled by the middleware for OPTIONS
    if request.method == 'OPTIONS':
        return jsonify({"status": "preflight_ok"})
    
    # For GET requests, return a response
    response = jsonify({
        "authenticated": False,
        "message": "Test endpoint"
    })
    
    # Add CORS headers to GET response as well
    origin = request.headers.get('Origin')
    if origin:
        response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    
    return response

# Test route with login_required to test authentication redirects
@app.route('/auth/protected', methods=['GET', 'OPTIONS'])
@login_required
def protected():
    """Protected route that requires authentication."""
    return jsonify({"authenticated": True})

if __name__ == '__main__':
    # Ensure host is 0.0.0.0 to allow external connections
    logger.info("Starting test server on http://localhost:5001")
    logger.info("Test URLs:")
    logger.info("- Public: http://localhost:5001/auth/current_user")
    logger.info("- Protected: http://localhost:5001/auth/protected")
    app.run(host='0.0.0.0', port=5001, debug=True)
