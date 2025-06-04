"""Social models for DoppleGänger
===========================

This module defines the social models and related database operations.
"""

import logging
from datetime import datetime
from flask import current_app
from extensions import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialProfile(db.Model):
    """Social profile model for storing user social profiles."""
    __tablename__ = 'social_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    profile_url = db.Column(db.String(255))
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='social_profiles')

    def __init__(self, user_id, platform, username, profile_url=None, is_verified=False):
        self.user_id = user_id
        self.platform = platform
        self.username = username
        self.profile_url = profile_url
        self.is_verified = is_verified

    def to_dict(self):
        """Convert profile to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'platform': self.platform,
            'username': self.username,
            'profile_url': self.profile_url,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def create(cls, user_id, platform, username, profile_url=None, is_verified=False):
        """Create a new social profile."""
        try:
            profile = cls(
                user_id=user_id,
                platform=platform,
                username=username,
                profile_url=profile_url,
                is_verified=is_verified
            )
            db.session.add(profile)
            db.session.commit()
            return profile
        except Exception as e:
            logger.error(f"Error creating social profile: {str(e)}")
            db.session.rollback()
            raise

    @classmethod
    def get_by_id(cls, profile_id):
        """Get a social profile by ID."""
        try:
            return cls.query.get(profile_id)
        except Exception as e:
            logger.error(f"Error getting social profile by ID: {str(e)}")
            raise

    @classmethod
    def get_by_user_id(cls, user_id):
        """Get social profiles for a user."""
        try:
            return cls.query.filter_by(user_id=user_id).all()
        except Exception as e:
            logger.error(f"Error getting social profiles by user ID: {str(e)}")
            raise

    @classmethod
    def get_by_platform(cls, platform):
        """Get social profiles for a platform."""
        try:
            return cls.query.filter_by(platform=platform).all()
        except Exception as e:
            logger.error(f"Error getting social profiles by platform: {str(e)}")
            raise

    def update(self, **kwargs):
        """Update a social profile."""
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return self
        except Exception as e:
            logger.error(f"Error updating social profile: {str(e)}")
            db.session.rollback()
            raise

    def delete(self):
        """Delete a social profile."""
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error deleting social profile: {str(e)}")
            db.session.rollback()
            raise

class SocialConnection(db.Model):
    """Social connection model for storing user connections."""
    __tablename__ = 'social_connections'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    connected_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    connection_type = db.Column(db.String(50), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='connections_given')
    connected_user = db.relationship('User', foreign_keys=[connected_user_id], backref='connections_received')

    def __init__(self, user_id, connected_user_id, connection_type, is_verified=False):
        self.user_id = user_id
        self.connected_user_id = connected_user_id
        self.connection_type = connection_type
        self.is_verified = is_verified

    def to_dict(self):
        """Convert connection to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'connected_user_id': self.connected_user_id,
            'connection_type': self.connection_type,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def create(cls, user_id, connected_user_id, connection_type, is_verified=False):
        """Create a new social connection."""
        try:
            connection = cls(
                user_id=user_id,
                connected_user_id=connected_user_id,
                connection_type=connection_type,
                is_verified=is_verified
            )
            db.session.add(connection)
            db.session.commit()
            return connection
        except Exception as e:
            logger.error(f"Error creating social connection: {str(e)}")
            db.session.rollback()
            raise

    @classmethod
    def get_by_id(cls, connection_id):
        """Get a social connection by ID."""
        try:
            return cls.query.get(connection_id)
        except Exception as e:
            logger.error(f"Error getting social connection by ID: {str(e)}")
            raise

    @classmethod
    def get_by_user_id(cls, user_id):
        """Get social connections for a user."""
        try:
            return cls.query.filter_by(user_id=user_id).all()
        except Exception as e:
            logger.error(f"Error getting social connections by user ID: {str(e)}")
            raise

    @classmethod
    def get_by_connected_user_id(cls, connected_user_id):
        """Get social connections where user is connected."""
        try:
            return cls.query.filter_by(connected_user_id=connected_user_id).all()
        except Exception as e:
            logger.error(f"Error getting social connections by connected user ID: {str(e)}")
            raise

    def verify(self):
        """Verify a social connection."""
        try:
            self.is_verified = True
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return self
        except Exception as e:
            logger.error(f"Error verifying social connection: {str(e)}")
            db.session.rollback()
            raise

    def delete(self):
        """Delete a social connection."""
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error deleting social connection: {str(e)}")
            db.session.rollback()
            raise
