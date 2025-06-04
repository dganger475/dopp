"""Notification models for DoppleGänger
===========================

This module defines the notification models and related database operations.
"""

import logging
from datetime import datetime
from flask import current_app
from extensions import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Notification(db.Model):
    """Notification model for storing user notifications."""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    notification_type = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='notifications_received')
    sender = db.relationship('User', foreign_keys=[sender_id], backref='notifications_sent')

    def __init__(self, user_id, notification_type, content=None, sender_id=None, is_read=False):
        self.user_id = user_id
        self.notification_type = notification_type
        self.content = content
        self.sender_id = sender_id
        self.is_read = is_read

    def to_dict(self):
        """Convert notification to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'sender_id': self.sender_id,
            'notification_type': self.notification_type,
            'content': self.content,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'sender': self.sender.to_dict() if self.sender else None
        }

    @classmethod
    def create(cls, user_id, notification_type, content=None, sender_id=None, is_read=False):
        """Create a new notification."""
        try:
            notification = cls(
                user_id=user_id,
                notification_type=notification_type,
                content=content,
                sender_id=sender_id,
                is_read=is_read
            )
            db.session.add(notification)
            db.session.commit()
            return notification
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")
            db.session.rollback()
            raise

    @classmethod
    def get_by_id(cls, notification_id):
        """Get a notification by ID."""
        try:
            return cls.query.get(notification_id)
        except Exception as e:
            logger.error(f"Error getting notification by ID: {str(e)}")
            raise

    @classmethod
    def get_by_user_id(cls, user_id, limit=20):
        """Get notifications for a user."""
        try:
            return cls.query.filter_by(user_id=user_id).order_by(
                cls.created_at.desc()
            ).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting notifications by user ID: {str(e)}")
            raise

    @classmethod
    def get_unread_count(cls, user_id):
        """Get the number of unread notifications for a user."""
        try:
            return cls.query.filter_by(
                user_id=user_id,
                is_read=False
            ).count()
        except Exception as e:
            logger.error(f"Error getting unread notification count: {str(e)}")
            raise

    def mark_as_read(self):
        """Mark a notification as read."""
        try:
            self.is_read = True
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return self
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            db.session.rollback()
            raise

    @classmethod
    def mark_all_as_read(cls, user_id):
        """Mark all notifications as read for a user."""
        try:
            cls.query.filter_by(
                user_id=user_id,
                is_read=False
            ).update({
                'is_read': True,
                'updated_at': datetime.utcnow()
            })
            db.session.commit()
        except Exception as e:
            logger.error(f"Error marking all notifications as read: {str(e)}")
            db.session.rollback()
            raise

    def delete(self):
        """Delete a notification."""
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error deleting notification: {str(e)}")
            db.session.rollback()
            raise 