"""Template Helpers
===============

This module provides helper functions for Jinja2 templates.
These functions are registered with the app and made available in templates.
"""

from datetime import datetime
from flask import url_for

def init_template_helpers(app):
    """Initialize template helper functions"""
    
    @app.template_filter('datetime')
    def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
        """Format a datetime object."""
        if value is None:
            return ""
        return value.strftime(format)
    
    @app.template_filter('timeago')
    def timeago(value):
        """Format datetime as relative time."""
        if value is None:
            return ""
        now = datetime.utcnow()
        diff = now - value
        
        if diff.days > 365:
            years = diff.days // 365
            return f"{years}y ago"
        if diff.days > 30:
            months = diff.days // 30
            return f"{months}mo ago"
        if diff.days > 0:
            return f"{diff.days}d ago"
        if diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        if diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        return "just now"
    
    @app.template_global()
    def static_url(filename):
        """Generate URL for static file with cache busting."""
        return url_for('static', filename=filename, v=app.config.get('VERSION', '1.0.0'))
    
    return app 