"""Security Middleware
================

This module provides security middleware to protect against common vulnerabilities.
"""

from functools import wraps
from flask import request, current_app, abort
import re
import bleach
from typing import Callable, Any, Optional, Union
import logging

def sanitize_input(input_text: str, is_email: bool = False, is_password: bool = False) -> str:
    """
    Sanitize input text to prevent XSS and other security issues.
    
    Args:
        input_text: The text to sanitize
        is_email: Whether the input is an email address
        is_password: Whether the input is a password
        
    Returns:
        Sanitized text
    """
    if not input_text:
        return ""
        
    # Convert to string if not already
    input_text = str(input_text)
    
    # Remove any null bytes
    input_text = input_text.replace('\0', '')
    
    # If it's an email, validate it
    if is_email:
        if not validate_email(input_text):
            return ""
        return input_text.lower().strip()
    
    # If it's a password, validate it
    if is_password:
        if not validate_password(input_text):
            return ""
        return input_text
    
    # For regular text, use bleach to sanitize
    allowed_tags = ['p', 'br', 'b', 'i', 'u', 'em', 'strong', 'a']
    allowed_attrs = {
        'a': ['href', 'title', 'target']
    }
    
    return bleach.clean(
        input_text,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True
    )

def validate_email(email: str) -> bool:
    """
    Validate an email address.
    
    Args:
        email: The email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False
        
    # Basic email validation regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password: str) -> bool:
    """
    Validate a password.
    
    Args:
        password: The password to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not password:
        return False
        
    # Password requirements:
    # - At least 8 characters
    # - At least one uppercase letter
    # - At least one lowercase letter
    # - At least one number
    # - At least one special character
    if len(password) < 8:
        return False
        
    if not re.search(r'[A-Z]', password):
        return False
        
    if not re.search(r'[a-z]', password):
        return False
        
    if not re.search(r'\d', password):
        return False
        
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
        
    return True

def secure_headers(response):
    """Add security headers to response."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response

def require_https(f: Callable) -> Callable:
    """Decorator to require HTTPS."""
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if not request.is_secure and not current_app.debug:
            abort(403, description="HTTPS required")
        return f(*args, **kwargs)
    return decorated_function

def prevent_sql_injection(input_text: str) -> str:
    """
    Prevent SQL injection by escaping special characters.
    
    Args:
        input_text: The text to escape
        
    Returns:
        Escaped text
    """
    if not input_text:
        return ""
        
    # Convert to string if not already
    input_text = str(input_text)
    
    # Escape SQL special characters
    input_text = input_text.replace("'", "''")  # Escape single quotes
    input_text = input_text.replace('"', '""')  # Escape double quotes
    input_text = input_text.replace('\\', '\\\\')  # Escape backslashes
    input_text = input_text.replace('%', '\\%')  # Escape percent signs
    input_text = input_text.replace('_', '\\_')  # Escape underscores
    
    # Remove SQL injection patterns
    patterns = [
        r'--.*$',  # SQL comments
        r';.*$',   # Multiple statements
        r'/\*.*\*/',  # Multi-line comments
        r'UNION.*SELECT',
        r'DROP.*TABLE',
        r'DELETE.*FROM',
        r'UPDATE.*SET',
        r'INSERT.*INTO'
    ]
    
    for pattern in patterns:
        input_text = re.sub(pattern, '', input_text, flags=re.IGNORECASE)
    
    return input_text

def rate_limit_by_ip(ip: str) -> bool:
    """
    Check if an IP address has exceeded the rate limit.
    
    Args:
        ip: The IP address to check
        
    Returns:
        True if rate limit exceeded, False otherwise
    """
    if not ip:
        return False
        
    # Get rate limit settings from config
    rate_limit = current_app.config.get('RATE_LIMIT', 100)
    rate_limit_window = current_app.config.get('RATE_LIMIT_WINDOW', 3600)  # 1 hour
    
    # TODO: Implement rate limiting logic using Redis or similar
    return False

def validate_json_schema(data: dict, schema: dict) -> bool:
    """
    Validate JSON data against a schema.
    
    Args:
        data: The JSON data to validate
        schema: The schema to validate against
        
    Returns:
        True if valid, False otherwise
    """
    if not data or not schema:
        return False
        
    # TODO: Implement JSON schema validation
    return True 