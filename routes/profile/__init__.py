"""Profile Routes Package
====================

This package contains all routes related to user profiles.
"""

from flask import Blueprint

# Create the profile blueprint
profile = Blueprint('profile', __name__, url_prefix='/profile')

# Import routes after creating the blueprint to avoid circular imports
from .view import profile_view
from .edit import edit_profile
from .helpers import helpers as profile_helpers
from .update import update_profile

# Register sub-blueprints if needed
profile.register_blueprint(edit_profile)

__all__ = ['profile', 'profile_view', 'edit_profile', 'profile_helpers', 'update_profile']
