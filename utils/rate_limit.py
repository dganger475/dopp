"""Rate Limiting Utilities
=====================

This module provides rate limiting functionality for API endpoints.
"""

import time
from typing import Dict, Tuple, Optional
from functools import wraps
from flask import request, current_app, jsonify

class RateLimiter:
    """Rate limiter for API endpoints."""
    
    def __init__(self, max_requests: int, window: int):
        """Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed in the window
            window: Time window in seconds
        """
        self.max_requests = max_requests
        self.window = window
        self.requests: Dict[str, list] = {}
        
    def _get_client_id(self) -> str:
        """Get client identifier from request."""
        # Try to get from X-Forwarded-For header first
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
            
        # Fall back to remote address
        return request.remote_addr
        
    def _cleanup_old_requests(self, client_id: str) -> None:
        """Remove requests outside the current window."""
        now = time.time()
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if now - req_time < self.window
        ]
        
    def is_rate_limited(self, client_id: str) -> Tuple[bool, Optional[int]]:
        """Check if client is rate limited.
        
        Returns:
            Tuple of (is_limited, retry_after)
        """
        now = time.time()
        
        # Initialize client requests if not exists
        if client_id not in self.requests:
            self.requests[client_id] = []
            
        # Cleanup old requests
        self._cleanup_old_requests(client_id)
        
        # Check if rate limited
        if len(self.requests[client_id]) >= self.max_requests:
            # Calculate retry after time
            oldest_request = min(self.requests[client_id])
            retry_after = int(oldest_request + self.window - now)
            return True, retry_after
            
        # Add current request
        self.requests[client_id].append(now)
        return False, None
        
    def limit(self, func):
        """Decorator to rate limit a function."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            client_id = self._get_client_id()
            is_limited, retry_after = self.is_rate_limited(client_id)
            
            if is_limited:
                return jsonify({
                    "error": "Rate limit exceeded",
                    "retry_after": retry_after
                }), 429
                
            return func(*args, **kwargs)
            
        return wrapper

def create_rate_limiter(max_requests: int, window: int) -> RateLimiter:
    """Create a rate limiter instance."""
    return RateLimiter(max_requests, window)

# Create default rate limiters
default_limiter = create_rate_limiter(100, 60)  # 100 requests per minute
strict_limiter = create_rate_limiter(10, 60)    # 10 requests per minute 