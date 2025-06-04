"""Follow models for DoppleGänger
===========================

This module defines the follow models and related database operations.
"""

import logging
from datetime import datetime
from flask import current_app
from extensions import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Follow(db.Model):
    """Follow model for storing user follows."""
    __tablename__ = 'follows'

    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    following_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    follower = db.relationship('User', foreign_keys=[follower_id], backref='following')
    following = db.relationship('User', foreign_keys=[following_id], backref='followers')

    def __init__(self, follower_id, following_id):
        self.follower_id = follower_id
        self.following_id = following_id

    def to_dict(self):
        """Convert follow to dictionary."""
        return {
            'id': self.id,
            'follower_id': self.follower_id,
            'following_id': self.following_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def create(cls, follower_id, following_id):
        """Create a new follow."""
        try:
            follow = cls(
                follower_id=follower_id,
                following_id=following_id
            )
            db.session.add(follow)
            db.session.commit()
            return follow
        except Exception as e:
            logger.error(f"Error creating follow: {str(e)}")
            db.session.rollback()
            raise

    @classmethod
    def get_by_id(cls, follow_id):
        """Get a follow by ID."""
        try:
            return cls.query.get(follow_id)
        except Exception as e:
            logger.error(f"Error getting follow by ID: {str(e)}")
            raise

    @classmethod
    def get_by_follower_id(cls, follower_id):
        """Get follows by a user."""
        try:
            return cls.query.filter_by(follower_id=follower_id).all()
        except Exception as e:
            logger.error(f"Error getting follows by follower ID: {str(e)}")
            raise

    @classmethod
    def get_by_following_id(cls, following_id):
        """Get followers of a user."""
        try:
            return cls.query.filter_by(following_id=following_id).all()
        except Exception as e:
            logger.error(f"Error getting follows by following ID: {str(e)}")
            raise

    @classmethod
    def get_follower_count(cls, user_id):
        """Get the number of followers for a user."""
        try:
            return cls.query.filter_by(following_id=user_id).count()
        except Exception as e:
            logger.error(f"Error getting follower count: {str(e)}")
            raise

    @classmethod
    def get_following_count(cls, user_id):
        """Get the number of users a user is following."""
        try:
            return cls.query.filter_by(follower_id=user_id).count()
        except Exception as e:
            logger.error(f"Error getting following count: {str(e)}")
            raise

    @classmethod
    def is_following(cls, follower_id, following_id):
        """Check if a user is following another user."""
        try:
            return cls.query.filter_by(
                follower_id=follower_id,
                following_id=following_id
            ).first() is not None
        except Exception as e:
            logger.error(f"Error checking if user is following: {str(e)}")
            raise

    def delete(self):
        """Delete a follow."""
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error deleting follow: {str(e)}")
            db.session.rollback()
            raise 