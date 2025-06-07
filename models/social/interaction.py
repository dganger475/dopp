"""Interaction models for DoppleGänger
===========================

This module defines the interaction models and related database operations.
"""

import logging
from datetime import datetime
from flask import current_app
from extensions import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Interaction(db.Model):
    """Interaction model for storing user interactions."""
    __tablename__ = 'interactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    interaction_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='interactions')
    target = db.relationship('User', foreign_keys=[target_id], backref='targeted_interactions')

    def __init__(self, user_id, target_id, interaction_type):
        self.user_id = user_id
        self.target_id = target_id
        self.interaction_type = interaction_type

    def to_dict(self):
        """Convert interaction to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'target_id': self.target_id,
            'interaction_type': self.interaction_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def create(cls, user_id, target_id, interaction_type):
        """Create a new interaction."""
        try:
            interaction = cls(
                user_id=user_id,
                target_id=target_id,
                interaction_type=interaction_type
            )
            db.session.add(interaction)
            db.session.commit()
            return interaction
        except Exception as e:
            logger.error(f"Error creating interaction: {str(e)}")
            db.session.rollback()
            raise

    @classmethod
    def get_by_id(cls, interaction_id):
        """Get an interaction by ID."""
        try:
            return cls.query.get(interaction_id)
        except Exception as e:
            logger.error(f"Error getting interaction by ID: {str(e)}")
            raise

    @classmethod
    def get_by_user_id(cls, user_id):
        """Get interactions for a user."""
        try:
            return cls.query.filter_by(user_id=user_id).order_by(
                cls.created_at.desc()
            ).all()
        except Exception as e:
            logger.error(f"Error getting interactions by user ID: {str(e)}")
            raise

    @classmethod
    def get_by_target_id(cls, target_id):
        """Get interactions targeting a user."""
        try:
            return cls.query.filter_by(target_id=target_id).order_by(
                cls.created_at.desc()
            ).all()
        except Exception as e:
            logger.error(f"Error getting interactions by target ID: {str(e)}")
            raise

    def update(self, **kwargs):
        """Update an interaction."""
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return self
        except Exception as e:
            logger.error(f"Error updating interaction: {str(e)}")
            db.session.rollback()
            raise

    def delete(self):
        """Delete an interaction."""
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error deleting interaction: {str(e)}")
            db.session.rollback()
            raise

    @classmethod
    def get_interaction_count(cls, user_id, target_id, interaction_type):
        """Get the number of interactions of a specific type between two users."""
        try:
            return cls.query.filter_by(
                user_id=user_id,
                target_id=target_id,
                interaction_type=interaction_type
            ).count()
        except Exception as e:
            logger.error(f"Error getting interaction count: {str(e)}")
            raise

    @classmethod
    def get_recent_interactions(cls, user_id, limit=10):
        """Get recent interactions for a user."""
        try:
            return cls.query.filter_by(user_id=user_id).order_by(
                cls.created_at.desc()
            ).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting recent interactions: {str(e)}")
            raise 