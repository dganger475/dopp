"""
Custom Exceptions
===============

This module contains all custom exceptions used throughout the application.
"""

class BaseAppException(Exception):
    """Base exception for all application exceptions"""
    def __init__(self, message, status_code=500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class ValidationError(BaseAppException):
    """Raised when data validation fails"""
    def __init__(self, message):
        super().__init__(message, status_code=400)

class AuthenticationError(BaseAppException):
    """Raised when authentication fails"""
    def __init__(self, message):
        super().__init__(message, status_code=401)

class AuthorizationError(BaseAppException):
    """Raised when user doesn't have required permissions"""
    def __init__(self, message):
        super().__init__(message, status_code=403)

class ResourceNotFoundError(BaseAppException):
    """Raised when requested resource is not found"""
    def __init__(self, message):
        super().__init__(message, status_code=404)

class FileUploadError(BaseAppException):
    """Raised when file upload fails"""
    def __init__(self, message):
        super().__init__(message, status_code=400)

class DatabaseError(BaseAppException):
    """Raised when database operations fail"""
    def __init__(self, message):
        super().__init__(message, status_code=500)

class RateLimitExceededError(BaseAppException):
    """Raised when rate limit is exceeded"""
    def __init__(self, message):
        super().__init__(message, status_code=429)

class ConfigurationError(BaseAppException):
    """Raised when there's a configuration error"""
    def __init__(self, message):
        super().__init__(message, status_code=500) 