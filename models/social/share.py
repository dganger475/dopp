"""Share models for DoppleGänger
===========================

This module defines the share models and related database operations.
"""

import logging
from datetime import datetime
from flask import current_app
from extensions import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Share(db.Model):
    """Share model for storing post shares."""
    __tablename__ = 'shares'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    share_type = db.Column(db.String(20), nullable=False)
    share_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='shares')
    post = db.relationship('Post', backref='shares')

    def __init__(self, post_id, user_id, share_type, share_url=None):
        self.post_id = post_id
        self.user_id = user_id
        self.share_type = share_type
        self.share_url = share_url

    def to_dict(self):
        """Convert share to dictionary."""
        return {
            'id': self.id,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'share_type': self.share_type,
            'share_url': self.share_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def create(cls, post_id, user_id, share_type, share_url=None):
        """Create a new share."""
        try:
            share = cls(
                post_id=post_id,
                user_id=user_id,
                share_type=share_type,
                share_url=share_url
            )
            db.session.add(share)
            db.session.commit()
            return share
        except Exception as e:
            logger.error(f"Error creating share: {str(e)}")
            db.session.rollback()
            raise

    @classmethod
    def get_by_id(cls, share_id):
        """Get a share by ID."""
        try:
            return cls.query.get(share_id)
        except Exception as e:
            logger.error(f"Error getting share by ID: {str(e)}")
            raise

    @classmethod
    def get_by_post_id(cls, post_id):
        """Get shares for a post."""
        try:
            return cls.query.filter_by(post_id=post_id).all()
        except Exception as e:
            logger.error(f"Error getting shares by post ID: {str(e)}")
            raise

    @classmethod
    def get_by_user_id(cls, user_id):
        """Get shares by a user."""
        try:
            return cls.query.filter_by(user_id=user_id).all()
        except Exception as e:
            logger.error(f"Error getting shares by user ID: {str(e)}")
            raise

    @classmethod
    def get_share_count(cls, post_id):
        """Get the number of shares for a post."""
        try:
            return cls.query.filter_by(post_id=post_id).count()
        except Exception as e:
            logger.error(f"Error getting share count: {str(e)}")
            raise

    def update(self, share_type=None, share_url=None):
        """Update a share."""
        try:
            if share_type is not None:
                self.share_type = share_type
            if share_url is not None:
                self.share_url = share_url
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return self
        except Exception as e:
            logger.error(f"Error updating share: {str(e)}")
            db.session.rollback()
            raise

    def delete(self):
        """Delete a share."""
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error deleting share: {str(e)}")
            db.session.rollback()
            raise 