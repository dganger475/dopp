"""
Models Package Initialization
============================

This package contains all the database models for the application.
"""

# Import the database instance from extensions
from extensions import db

# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .face import Face
from .follow import Follow
from .notification import Notification
from .reaction import Reaction
from .social import Post, Comment, Like, ClaimedProfile
from .user_match import UserMatch

# Make models available at the package level
__all__ = [
    'db',
    'User',
    'Face',
    'Follow',
    'Notification',
    'Reaction',
    'Post',
    'Comment',
    'Like',
    'ClaimedProfile',
    'UserMatch'
]