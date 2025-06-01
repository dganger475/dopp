"""Logging Utilities
===============

This module provides structured logging functionality for the application.
"""

import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from functools import wraps

class StructuredLogger:
    """Structured logger for consistent log formatting."""
    
    def __init__(self, name: str):
        """Initialize logger with name."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(handler)
        
    def _format_message(self, message: str, **kwargs) -> str:
        """Format message with additional context."""
        data = {
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        return json.dumps(data)
        
    def info(self, message: str, **kwargs) -> None:
        """Log info message with context."""
        self.logger.info(self._format_message(message, **kwargs))
        
    def error(self, message: str, exc_info: Optional[Exception] = None, **kwargs) -> None:
        """Log error message with context and exception info."""
        if exc_info:
            kwargs["exception"] = {
                "type": type(exc_info).__name__,
                "message": str(exc_info),
                "traceback": traceback.format_exc()
            }
        self.logger.error(self._format_message(message, **kwargs))
        
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with context."""
        self.logger.warning(self._format_message(message, **kwargs))
        
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with context."""
        self.logger.debug(self._format_message(message, **kwargs))

def log_execution(logger: StructuredLogger):
    """Decorator to log function execution."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Log function call
            logger.info(
                f"Executing {func.__name__}",
                function=func.__name__,
                args=args,
                kwargs=kwargs
            )
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Log success
                logger.info(
                    f"Successfully executed {func.__name__}",
                    function=func.__name__,
                    result=result
                )
                
                return result
                
            except Exception as e:
                # Log error
                logger.error(
                    f"Error executing {func.__name__}",
                    exc_info=e,
                    function=func.__name__,
                    args=args,
                    kwargs=kwargs
                )
                raise
                
        return wrapper
    return decorator

def setup_logging(app):
    """Setup logging for the application."""
    # Create loggers for different components
    app.logger = StructuredLogger("app")
    app.logger.info("Application logging initialized")
    
    # Create loggers for other components
    loggers = {
        "database": StructuredLogger("database"),
        "social": StructuredLogger("social"),
        "user": StructuredLogger("user"),
        "api": StructuredLogger("api")
    }
    
    # Add loggers to app context
    app.loggers = loggers
    
    return app

# Create default logger
logger = StructuredLogger("default") 