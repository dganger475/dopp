"""Like models for DoppleGänger
===========================

This module defines the like models and related database operations.
"""

import logging
from datetime import datetime
from flask import current_app
from extensions import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Like(db.Model):
    """Like model for storing post likes."""
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='likes')
    post = db.relationship('Post', backref='likes')

    def __init__(self, post_id, user_id):
        self.post_id = post_id
        self.user_id = user_id

    def to_dict(self):
        """Convert like to dictionary."""
        return {
            'id': self.id,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def create(cls, post_id, user_id):
        """Create a new like."""
        try:
            like = cls(
                post_id=post_id,
                user_id=user_id
            )
            db.session.add(like)
            db.session.commit()
            return like
        except Exception as e:
            logger.error(f"Error creating like: {str(e)}")
            db.session.rollback()
            raise

    @classmethod
    def get_by_id(cls, like_id):
        """Get a like by ID."""
        try:
            return cls.query.get(like_id)
        except Exception as e:
            logger.error(f"Error getting like by ID: {str(e)}")
            raise

    @classmethod
    def get_by_post_id(cls, post_id):
        """Get likes for a post."""
        try:
            return cls.query.filter_by(post_id=post_id).all()
        except Exception as e:
            logger.error(f"Error getting likes by post ID: {str(e)}")
            raise

    @classmethod
    def get_by_user_id(cls, user_id):
        """Get likes by a user."""
        try:
            return cls.query.filter_by(user_id=user_id).all()
        except Exception as e:
            logger.error(f"Error getting likes by user ID: {str(e)}")
            raise

    @classmethod
    def get_like_count(cls, post_id):
        """Get the number of likes for a post."""
        try:
            return cls.query.filter_by(post_id=post_id).count()
        except Exception as e:
            logger.error(f"Error getting like count: {str(e)}")
            raise

    @classmethod
    def has_liked(cls, post_id, user_id):
        """Check if a user has liked a post."""
        try:
            return cls.query.filter_by(
                post_id=post_id,
                user_id=user_id
            ).first() is not None
        except Exception as e:
            logger.error(f"Error checking if user has liked post: {str(e)}")
            raise

    def delete(self):
        """Delete a like."""
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error deleting like: {str(e)}")
            db.session.rollback()
            raise 