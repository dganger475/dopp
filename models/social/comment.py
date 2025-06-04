"""Comment models for DoppleGänger
===========================

This module defines the comment models and related database operations.
"""

import logging
from datetime import datetime
from flask import current_app
from extensions import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Comment(db.Model):
    """Comment model for storing post comments."""
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='comments')
    post = db.relationship('Post', backref='comments')
    parent = db.relationship('Comment', remote_side=[id], backref='replies')

    def __init__(self, post_id, user_id, content, parent_id=None):
        self.post_id = post_id
        self.user_id = user_id
        self.content = content
        self.parent_id = parent_id

    def to_dict(self):
        """Convert comment to dictionary."""
        return {
            'id': self.id,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'content': self.content,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user': self.user.to_dict() if self.user else None,
            'replies': [reply.to_dict() for reply in self.replies] if self.replies else []
        }

    @classmethod
    def create(cls, post_id, user_id, content, parent_id=None):
        """Create a new comment."""
        try:
            comment = cls(
                post_id=post_id,
                user_id=user_id,
                content=content,
                parent_id=parent_id
            )
            db.session.add(comment)
            db.session.commit()
            return comment
        except Exception as e:
            logger.error(f"Error creating comment: {str(e)}")
            db.session.rollback()
            raise

    @classmethod
    def get_by_id(cls, comment_id):
        """Get a comment by ID."""
        try:
            return cls.query.get(comment_id)
        except Exception as e:
            logger.error(f"Error getting comment by ID: {str(e)}")
            raise

    @classmethod
    def get_by_post_id(cls, post_id):
        """Get comments for a post."""
        try:
            return cls.query.filter_by(
                post_id=post_id,
                parent_id=None
            ).order_by(cls.created_at.desc()).all()
        except Exception as e:
            logger.error(f"Error getting comments by post ID: {str(e)}")
            raise

    @classmethod
    def get_by_user_id(cls, user_id):
        """Get comments by a user."""
        try:
            return cls.query.filter_by(user_id=user_id).order_by(
                cls.created_at.desc()
            ).all()
        except Exception as e:
            logger.error(f"Error getting comments by user ID: {str(e)}")
            raise

    def update(self, content):
        """Update a comment."""
        try:
            self.content = content
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return self
        except Exception as e:
            logger.error(f"Error updating comment: {str(e)}")
            db.session.rollback()
            raise

    def delete(self):
        """Delete a comment."""
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error deleting comment: {str(e)}")
            db.session.rollback()
            raise

    @classmethod
    def get_replies(cls, comment_id):
        """Get replies to a comment."""
        try:
            return cls.query.filter_by(parent_id=comment_id).order_by(
                cls.created_at.asc()
            ).all()
        except Exception as e:
            logger.error(f"Error getting comment replies: {str(e)}")
            raise 