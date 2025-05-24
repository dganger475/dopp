"""
Social Module
============

This module contains all social-related functionality, including:
- Feed management
- Post interactions
- Notifications
- Social utilities
"""
from flask import Blueprint

# Create the main social blueprint
social = Blueprint('social', __name__)

# If you have a create_post function, import it here
from .post import create_post

# Then register the route
social.add_url_rule('/create_post', view_func=create_post, methods=['GET', 'POST'])

# Import and register sub-blueprints
from .feed import feed
from .interactions import interactions
from .notifications import notifications
from .friends import friends
from .matches import matches

# Register sub-blueprints with the main social blueprint
social.register_blueprint(feed, url_prefix='/feed', strict_slashes=False)
social.register_blueprint(interactions, url_prefix='/interactions')
social.register_blueprint(notifications, url_prefix='/notifications')
social.register_blueprint(friends, url_prefix='/friends')
social.register_blueprint(matches, url_prefix='/matches')

# Import routes after blueprint creation to avoid circular imports
from . import feed, interactions, notifications
