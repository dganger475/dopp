"""
Base SQLAlchemy models for the application.
This module provides the SQLAlchemy database instance and base model class.
"""

from extensions import db, migrate

# Import models to ensure they're registered with SQLAlchemy
from .user import User
from .face import Face
from .follow import Follow
from .notification import Notification
from .reaction import Reaction
from .social import Post, Comment, Like, SavedPost, UserMatch

# Create a declarative base model class
Base = db.Model

# This is kept for backward compatibility
def init_db(app):
    """Initialize the database with the Flask app.
    
    Note: This function is kept for backward compatibility.
    Use extensions.init_extensions() instead.
    """
    from extensions import init_extensions
    return init_extensions(app)
