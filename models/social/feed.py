"""Feed models for DoppleGänger
===========================

This module defines the feed models and related database operations.
"""

import logging
from datetime import datetime
from flask import current_app
from extensions import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Feed(db.Model):
    """Feed model for storing user feeds."""
    __tablename__ = 'feeds'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)
    content_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='feeds')

    def __init__(self, user_id, content_type, content_id):
        self.user_id = user_id
        self.content_type = content_type
        self.content_id = content_id

    def to_dict(self):
        """Convert feed to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def create(cls, user_id, content_type, content_id):
        """Create a new feed item."""
        try:
            feed = cls(
                user_id=user_id,
                content_type=content_type,
                content_id=content_id
            )
            db.session.add(feed)
            db.session.commit()
            return feed
        except Exception as e:
            logger.error(f"Error creating feed item: {str(e)}")
            db.session.rollback()
            raise

    @classmethod
    def get_by_id(cls, feed_id):
        """Get a feed item by ID."""
        try:
            return cls.query.get(feed_id)
        except Exception as e:
            logger.error(f"Error getting feed item by ID: {str(e)}")
            raise

    @classmethod
    def get_by_user_id(cls, user_id, limit=20):
        """Get feed items for a user."""
        try:
            return cls.query.filter_by(user_id=user_id).order_by(
                cls.created_at.desc()
            ).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting feed items by user ID: {str(e)}")
            raise

    @classmethod
    def get_recent_feed(cls, user_id, limit=20):
        """Get recent feed items for a user."""
        try:
            return cls.query.filter_by(user_id=user_id).order_by(
                cls.created_at.desc()
            ).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting recent feed items: {str(e)}")
            raise

    def delete(self):
        """Delete a feed item."""
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error deleting feed item: {str(e)}")
            db.session.rollback()
            raise

class FeedItem(db.Model):
    """Feed item model for storing feed item details."""
    __tablename__ = 'feed_items'

    id = db.Column(db.Integer, primary_key=True)
    feed_id = db.Column(db.Integer, db.ForeignKey('feeds.id'), nullable=False)
    item_type = db.Column(db.String(50), nullable=False)
    item_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    feed = db.relationship('Feed', backref='items')

    def __init__(self, feed_id, item_type, item_id):
        self.feed_id = feed_id
        self.item_type = item_type
        self.item_id = item_id

    def to_dict(self):
        """Convert feed item to dictionary."""
        return {
            'id': self.id,
            'feed_id': self.feed_id,
            'item_type': self.item_type,
            'item_id': self.item_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def create(cls, feed_id, item_type, item_id):
        """Create a new feed item."""
        try:
            item = cls(
                feed_id=feed_id,
                item_type=item_type,
                item_id=item_id
            )
            db.session.add(item)
            db.session.commit()
            return item
        except Exception as e:
            logger.error(f"Error creating feed item: {str(e)}")
            db.session.rollback()
            raise

    @classmethod
    def get_by_id(cls, item_id):
        """Get a feed item by ID."""
        try:
            return cls.query.get(item_id)
        except Exception as e:
            logger.error(f"Error getting feed item by ID: {str(e)}")
            raise

    @classmethod
    def get_by_feed_id(cls, feed_id):
        """Get feed items for a feed."""
        try:
            return cls.query.filter_by(feed_id=feed_id).order_by(
                cls.created_at.desc()
            ).all()
        except Exception as e:
            logger.error(f"Error getting feed items by feed ID: {str(e)}")
            raise

    def delete(self):
        """Delete a feed item."""
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error deleting feed item: {str(e)}")
            db.session.rollback()
            raise 