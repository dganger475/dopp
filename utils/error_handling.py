"""Error Handling
=============

This module provides centralized error handling functionality.
"""

from typing import Dict, Any, Optional, Type
from flask import jsonify, current_app
import traceback
import sys
from datetime import datetime
import json

class AppError(Exception):
    """Base application error class."""
    
    def __init__(self, message: str, status_code: int = 500, error_code: Optional[str] = None):
        """Initialize error."""
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.timestamp = datetime.utcnow()
        
class ValidationError(AppError):
    """Validation error."""
    def __init__(self, message: str):
        super().__init__(message, status_code=400, error_code='VALIDATION_ERROR')
        
class AuthenticationError(AppError):
    """Authentication error."""
    def __init__(self, message: str):
        super().__init__(message, status_code=401, error_code='AUTHENTICATION_ERROR')
        
class AuthorizationError(AppError):
    """Authorization error."""
    def __init__(self, message: str):
        super().__init__(message, status_code=403, error_code='AUTHORIZATION_ERROR')
        
class NotFoundError(AppError):
    """Resource not found error."""
    def __init__(self, message: str):
        super().__init__(message, status_code=404, error_code='NOT_FOUND')
        
class RateLimitError(AppError):
    """Rate limit error."""
    def __init__(self, message: str):
        super().__init__(message, status_code=429, error_code='RATE_LIMIT_EXCEEDED')

def handle_error(error: Exception) -> tuple:
    """Handle application errors."""
    if isinstance(error, AppError):
        response = {
            'error': {
                'code': error.error_code,
                'message': error.message,
                'timestamp': error.timestamp.isoformat()
            }
        }
        return jsonify(response), error.status_code
        
    # Handle unexpected errors
    current_app.logger.error(f"Unexpected error: {str(error)}")
    current_app.logger.error(traceback.format_exc())
    
    response = {
        'error': {
            'code': 'INTERNAL_SERVER_ERROR',
            'message': 'An unexpected error occurred',
            'timestamp': datetime.utcnow().isoformat()
        }
    }
    
    if current_app.debug:
        response['error']['traceback'] = traceback.format_exc()
        
    return jsonify(response), 500

def register_error_handlers(app):
    """Register error handlers with Flask app."""
    app.register_error_handler(AppError, handle_error)
    app.register_error_handler(Exception, handle_error)
    
    @app.errorhandler(404)
    def not_found_error(error):
        return handle_error(NotFoundError("Resource not found"))
        
    @app.errorhandler(405)
    def method_not_allowed_error(error):
        return handle_error(AppError("Method not allowed", status_code=405, error_code='METHOD_NOT_ALLOWED'))
        
    @app.errorhandler(500)
    def internal_server_error(error):
        return handle_error(AppError("Internal server error", status_code=500, error_code='INTERNAL_SERVER_ERROR'))

def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
    """Log error with context."""
    error_data = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'timestamp': datetime.utcnow().isoformat(),
        'traceback': traceback.format_exc()
    }
    
    if context:
        error_data['context'] = context
        
    current_app.logger.error(json.dumps(error_data)) 