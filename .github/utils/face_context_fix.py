"""
This module provides a function to safely extract face encodings with proper Flask app context.
It's a utility to ensure threads don't have app context issues.
"""

import threading
from functools import wraps

from flask import current_app


def extract_with_app_context(extract_func):
    """
    A decorator that ensures the extraction function runs with a proper Flask app context.
    This fixes the "Working outside of application context" error.
    """

    @wraps(extract_func)
    def wrapper(*args, **kwargs):
        # If we're already in app context, just run the function
        try:
            return extract_func(*args, **kwargs)
        except RuntimeError as e:
            # If we get an app context error, get the app and create a context
            if "Working outside of application context" in str(e):
                # Get the current app
                app = current_app._get_current_object()
                with app.app_context():
                    return extract_func(*args, **kwargs)
            else:
                # Re-raise any other RuntimeError
                raise

    return wrapper


def run_with_app_context(func, *args, **kwargs):
    """
    Run the given function with proper Flask application context.
    This is useful for running functions in threads.
    """
    try:
        # Try running directly
        return func(*args, **kwargs)
    except RuntimeError as e:
        # If we get an app context error, get the app and create a context
        if "Working outside of application context" in str(e):
            # Get the current app
            app = current_app._get_current_object()
            with app.app_context():
                return func(*args, **kwargs)
        else:
            # Re-raise any other RuntimeError
            raise
