"""Post Models
============

Defines models for social media posts and related operations.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from models.user import User
from extensions import db
from utils.template_utils import get_image_path
from utils.image_paths import normalize_extracted_face_path
from utils.serializers import serialize_match_card

class Post(db.Model):
    """Model for social media posts."""
    __tablename__ = 'posts'
    __table_args__ = {'extend_existing': True}  # Allow table to be redefined

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_match_post = db.Column(db.Boolean, default=False)
    face_filename = db.Column(db.String(255))

    # Relationships with back_populates to avoid conflicts
    user = db.relationship('User', back_populates='posts', overlaps="post_author,user_posts")
    comments = db.relationship('Comment', back_populates='post', lazy=True, cascade='all, delete-orphan')
    likes = db.relationship('Like', back_populates='post', lazy=True, cascade='all, delete-orphan', overlaps="post_ref,post_likes")

    def __repr__(self):
        return f'<Post {self.id}>'

    @property
    def likes_count(self):
        """Get the number of likes for this post."""
        return len(self.likes) if self.likes else 0

    @classmethod
    def get_by_id(cls, post_id: int) -> Optional['Post']:
        """Get a post by its ID."""
        return cls.query.get(post_id)

    @classmethod
    def create(cls, user_id: int, content: str, face_filename: str = None, is_match_post: bool = False) -> Optional['Post']:
        """Create a new post."""
        try:
            post = cls(
                user_id=user_id,
                content=content,
                face_filename=face_filename,
                is_match_post=is_match_post
            )
            db.session.add(post)
            db.session.commit()
            return post
        except Exception as e:
            logging.error(f"Error creating post: {e}", exc_info=True)
            db.session.rollback()
            return None

    @classmethod
    def get_feed(cls, limit: int = 20, offset: int = 0) -> List['Post']:
        """Get the latest posts for the main feed."""
        try:
            return cls.query.order_by(cls.created_at.desc()).limit(limit).offset(offset).all()
        except Exception as e:
            logging.error(f"Error fetching feed: {e}")
            return []

    @classmethod
    def get_user_posts(cls, user_id: int, limit: int = 20, offset: int = 0) -> List['Post']:
        """Get posts by a specific user."""
        try:
            return cls.query.filter_by(user_id=user_id).order_by(cls.created_at.desc()).limit(limit).offset(offset).all()
        except Exception as e:
            logging.error(f"Error fetching user posts: {e}")
            return []

    def update(self, content: str) -> bool:
        """Update the post content."""
        try:
            self.content = content
            db.session.commit()
            return True
        except Exception as e:
            logging.error(f"Error updating post: {e}")
            db.session.rollback()
            return False

    def delete(self) -> bool:
        """Delete the post and associated data."""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            logging.error(f"Error deleting post: {e}")
            db.session.rollback()
            return False

    def to_dict(self, user_id=None, include_comments=True):
        """Convert post to dictionary."""
        from models.face import Face
        # User face image (profile image)
        user_face_image_url = self.user.get_profile_image_url() if self.user else '/static/images/default_profile.svg'

        # Sanitize face_filename by stripping query string if present
        face_filename_clean = self.face_filename.split('?')[0] if self.face_filename and '?' in self.face_filename else self.face_filename

        # Match face image (from faces table)
        match_face_image_url = '/static/images/default_profile.svg'
        match_face_id = None
        logger = logging.getLogger("Post.to_dict")
        logger.debug(f"Post {self.id}: face_filename={self.face_filename}")
        if self.face_filename:
            face = Face.get_by_filename(face_filename_clean)
            if face and face.filename:
                match_face_image_url = f"/static/extracted_faces/{face.filename}"
                match_face_id = face.id
                logger.info(f"Post {self.id}: Found face record for filename '{face_filename_clean}', using normalized URL: {match_face_image_url}")
            else:
                logger.warning(f"Post {self.id}: No face record found for filename '{face_filename_clean}', using normalized fallback URL: /static/default_profile.png")
        logger.debug(f"Post {self.id}: Final match_face_image_url: {match_face_image_url}")

        # --- Unified match card ---
        match_card = None
        if self.face_filename:
            face = Face.get_by_filename(face_filename_clean)
            if face:
                match_card = serialize_match_card(face, None, getattr(self, 'similarity', None))
            else:
                # fallback: minimal card with filename
                match_card = {
                    "id": None,
                    "image": match_face_image_url,
                    "username": face_filename_clean,
                    "label": "UNCLAIMED PROFILE",
                    "similarity": None,
                    "stateDecade": ""
                }

        d = {
            'id': self.id,
            'user_id': self.user_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if hasattr(self.created_at, 'isoformat') else str(self.created_at),
            'is_match_post': self.is_match_post,
            'face_filename': self.face_filename,
            'likes_count': getattr(self, 'likes_count', 0),
            'user_has_liked': any(like.user_id == user_id for like in self.likes) if user_id and self.likes else False,
            'user': self.user.to_dict() if self.user else {},
            'user_face_image_url': user_face_image_url,
            'match_face_image_url': match_face_image_url,
            'match_face_id': match_face_id,
            'comments': [c.to_dict() for c in self.comments] if include_comments and hasattr(self, 'comments') else [],
            'match_card': match_card
        }
        return d

class PostImage:
    """Model for post images."""
    pass

class PostReaction:
    """Model for post reactions."""
    pass 