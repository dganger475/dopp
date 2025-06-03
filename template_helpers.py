"""Template Helpers Module
===========================

This module provides template helper functions that are used across the application's templates.
These functions are registered with Flask's template context.
"""

from flask import current_app
from utils.image_urls import get_face_image_url, get_profile_image_url
from utils.files.utils import generate_face_filename, is_anonymized_face_filename, parse_face_id_from_filename

def init_template_helpers(app):
    """Initialize template helper functions with the Flask application.
    
    Args:
        app: Flask application instance
    """
    @app.context_processor
    def utility_processor():
        """Register template helper functions with Flask's template context."""
        return {
            'get_face_image_url': get_face_image_url,
            'get_profile_image_url': get_profile_image_url,
            'generate_face_filename': generate_face_filename,
            'is_anonymized_face_filename': is_anonymized_face_filename,
            'parse_face_id_from_filename': parse_face_id_from_filename
        } 