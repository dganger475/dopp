"""Post models for DoppleGänger
===========================

This module defines the post models and related database operations.
"""

import logging
from datetime import datetime
from flask import current_app
from extensions import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Post(db.Model):
    """Post model for storing user posts."""
    __tablename__ = 'posts'
    __table_args__ = (
        db.Index('idx_posts_user_id', 'user_id'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text)
    visibility = db.Column(db.String(20), default='public')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('posts', lazy='dynamic'))
    images = db.relationship('PostImage', backref='post', cascade='all, delete-orphan')
    reactions = db.relationship('PostReaction', backref='post', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='post', cascade='all, delete-orphan')

    def __init__(self, user_id, content=None, visibility='public'):
        self.user_id = user_id
        self.content = content
        self.visibility = visibility

    def to_dict(self):
        """Convert post to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content': self.content,
            'visibility': self.visibility,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'images': [image.to_dict() for image in self.images],
            'reactions': [reaction.to_dict() for reaction in self.reactions],
            'comments': [comment.to_dict() for comment in self.comments]
        }

    @classmethod
    def create(cls, user_id, content=None, visibility='public'):
        """Create a new post."""
        try:
            post = cls(
                user_id=user_id,
                content=content,
                visibility=visibility
            )
            db.session.add(post)
            db.session.commit()
            return post
        except Exception as e:
            logger.error(f"Error creating post: {str(e)}")
            db.session.rollback()
            raise

    @classmethod
    def get_by_id(cls, post_id):
        """Get a post by ID."""
        try:
            return cls.query.get(post_id)
        except Exception as e:
            logger.error(f"Error getting post by ID: {str(e)}")
            raise

    @classmethod
    def get_by_user_id(cls, user_id, limit=20):
        """Get posts for a user."""
        try:
            return cls.query.filter_by(user_id=user_id).order_by(
                cls.created_at.desc()
            ).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting posts by user ID: {str(e)}")
            raise

    def update(self, **kwargs):
        """Update a post."""
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return self
        except Exception as e:
            logger.error(f"Error updating post: {str(e)}")
            db.session.rollback()
            raise

    def delete(self):
        """Delete a post."""
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error deleting post: {str(e)}")
            db.session.rollback()
            raise

class PostImage(db.Model):
    """Post image model for storing post images."""
    __tablename__ = 'post_images'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(255))
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, post_id, image_url, caption=None, order=0):
        self.post_id = post_id
        self.image_url = image_url
        self.caption = caption
        self.order = order

    def to_dict(self):
        """Convert image to dictionary."""
        return {
            'id': self.id,
            'post_id': self.post_id,
            'image_url': self.image_url,
            'caption': self.caption,
            'order': self.order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def create(cls, post_id, image_url, caption=None, order=0):
        """Create a new post image."""
        try:
            image = cls(
                post_id=post_id,
                image_url=image_url,
                caption=caption,
                order=order
            )
            db.session.add(image)
            db.session.commit()
            return image
        except Exception as e:
            logger.error(f"Error creating post image: {str(e)}")
            db.session.rollback()
            raise

    @classmethod
    def get_by_id(cls, image_id):
        """Get a post image by ID."""
        try:
            return cls.query.get(image_id)
        except Exception as e:
            logger.error(f"Error getting post image by ID: {str(e)}")
            raise

    @classmethod
    def get_by_post_id(cls, post_id):
        """Get images for a post."""
        try:
            return cls.query.filter_by(post_id=post_id).order_by(cls.order).all()
        except Exception as e:
            logger.error(f"Error getting post images by post ID: {str(e)}")
            raise

    def update(self, **kwargs):
        """Update a post image."""
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return self
        except Exception as e:
            logger.error(f"Error updating post image: {str(e)}")
            db.session.rollback()
            raise

    def delete(self):
        """Delete a post image."""
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error deleting post image: {str(e)}")
            db.session.rollback()
            raise

class PostReaction(db.Model):
    """Post reaction model for storing post reactions."""
    __tablename__ = 'post_reactions'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reaction_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='post_reactions')

    def __init__(self, post_id, user_id, reaction_type):
        self.post_id = post_id
        self.user_id = user_id
        self.reaction_type = reaction_type

    def to_dict(self):
        """Convert reaction to dictionary."""
        return {
            'id': self.id,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'reaction_type': self.reaction_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def create(cls, post_id, user_id, reaction_type):
        """Create a new post reaction."""
        try:
            reaction = cls(
                post_id=post_id,
                user_id=user_id,
                reaction_type=reaction_type
            )
            db.session.add(reaction)
            db.session.commit()
            return reaction
        except Exception as e:
            logger.error(f"Error creating post reaction: {str(e)}")
            db.session.rollback()
            raise

    @classmethod
    def get_by_id(cls, reaction_id):
        """Get a post reaction by ID."""
        try:
            return cls.query.get(reaction_id)
        except Exception as e:
            logger.error(f"Error getting post reaction by ID: {str(e)}")
            raise

    @classmethod
    def get_by_post_id(cls, post_id):
        """Get reactions for a post."""
        try:
            return cls.query.filter_by(post_id=post_id).all()
        except Exception as e:
            logger.error(f"Error getting post reactions by post ID: {str(e)}")
            raise

    @classmethod
    def get_by_user_id(cls, user_id):
        """Get reactions by a user."""
        try:
            return cls.query.filter_by(user_id=user_id).all()
        except Exception as e:
            logger.error(f"Error getting post reactions by user ID: {str(e)}")
            raise

    def update(self, reaction_type):
        """Update a post reaction."""
        try:
            self.reaction_type = reaction_type
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return self
        except Exception as e:
            logger.error(f"Error updating post reaction: {str(e)}")
            db.session.rollback()
            raise

    def delete(self):
        """Delete a post reaction."""
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error deleting post reaction: {str(e)}")
            db.session.rollback()
            raise 