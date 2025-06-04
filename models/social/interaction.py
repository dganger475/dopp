"""Social Interaction Models
=======================

Defines models for social interactions like comments and likes.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from flask import current_app

from extensions import db
from models.user import User
from utils.db.database import get_users_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Interaction(db.Model):
    """Interaction model for storing user interactions."""
    __tablename__ = 'interactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    interaction_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='interactions_given')
    target = db.relationship('User', foreign_keys=[target_id], backref='interactions_received')

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
        """Get interactions given by a user."""
        try:
            return cls.query.filter_by(user_id=user_id).all()
        except Exception as e:
            logger.error(f"Error getting interactions by user ID: {str(e)}")
            raise

    @classmethod
    def get_by_target_id(cls, target_id):
        """Get interactions received by a user."""
        try:
            return cls.query.filter_by(target_id=target_id).all()
        except Exception as e:
            logger.error(f"Error getting interactions by target ID: {str(e)}")
            raise

    def update(self, interaction_type=None):
        """Update an interaction."""
        try:
            if interaction_type is not None:
                self.interaction_type = interaction_type
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

class Comment(db.Model):
    """Model for post comments."""
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    post = db.relationship('Post', backref=db.backref('comments', lazy=True))

    @classmethod
    def get_by_id(cls, comment_id: int) -> Optional['Comment']:
        """Get a comment by its ID."""
        return cls.query.get(comment_id)

    @classmethod
    def get_for_post(cls, post_id: int) -> List['Comment']:
        """Get all comments for a post."""
        return cls.query.filter_by(post_id=post_id).all()

    @classmethod
    def create(cls, post_id: int, user_id: int, content: str) -> Optional['Comment']:
        """Create a new comment."""
        try:
            comment = cls(
                post_id=post_id,
                user_id=user_id,
                content=content
            )
            db.session.add(comment)
            db.session.commit()
            return comment
        except Exception as e:
            logging.error(f"Error creating comment: {e}", exc_info=True)
            db.session.rollback()
            return None

    def update(self, content: str) -> bool:
        """Update the comment content."""
        try:
            self.content = content
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        except Exception as e:
            logging.error(f"Error updating comment: {e}")
            db.session.rollback()
            return False

    def delete(self) -> bool:
        """Delete the comment."""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            logging.error(f"Error deleting comment: {e}")
            db.session.rollback()
            return False

    def get_user(self) -> Optional[User]:
        """Get the user who created this comment."""
        return User.query.get(self.user_id)

    def to_dict(self, include_user: bool = True) -> Dict[str, Any]:
        """Convert comment to dictionary for JSON response."""
        data = {
            'id': self.id,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_user and self.user:
            data['user'] = {
                'id': self.user.id,
                'username': self.user.username,
                'profile_image': self.user.profile_image
            }

        return data

class Like(db.Model):
    """Model for post likes."""
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('likes', lazy=True))
    post = db.relationship('Post', backref=db.backref('likes', lazy=True))

    @classmethod
    def get_by_id(cls, like_id: int) -> Optional['Like']:
        """Get a like by its ID."""
        return cls.query.get(like_id)

    @classmethod
    def create(cls, post_id: int, user_id: int) -> Optional['Like']:
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
            logging.error(f"Error creating like: {e}", exc_info=True)
            db.session.rollback()
            return None

    def delete(self) -> bool:
        """Delete the like."""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            logging.error(f"Error deleting like: {e}")
            db.session.rollback()
            return False

    def to_dict(self, include_user: bool = True) -> Dict[str, Any]:
        """Convert like to dictionary for JSON response."""
        data = {
            'id': self.id,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

        if include_user and self.user:
            data['user'] = {
                'id': self.user.id,
                'username': self.user.username,
                'profile_image': self.user.profile_image
            }

        return data

class Reaction:
    """Model for post reactions."""

    TYPES = ["like", "love", "haha", "wow", "sad", "angry"]

    @staticmethod
    def create(post_id: int, user_id: int, reaction_type: str) -> bool:
        """Create a new reaction."""
        if reaction_type not in Reaction.TYPES:
            return False

        conn = get_users_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO reactions (post_id, user_id, reaction_type, created_at)
                VALUES (?, ?, ?, datetime('now'))
                """,
                (post_id, user_id, reaction_type),
            )

            conn.commit()
            return True

        except Exception as e:
            logging.error(f"Error creating reaction: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def update(post_id: int, user_id: int, reaction_type: str) -> bool:
        """Update an existing reaction."""
        if reaction_type not in Reaction.TYPES:
            return False

        conn = get_users_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE reactions 
                SET reaction_type = ?, created_at = datetime('now')
                WHERE post_id = ? AND user_id = ?
                """,
                (reaction_type, post_id, user_id),
            )

            conn.commit()
            return True

        except Exception as e:
            logging.error(f"Error updating reaction: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def delete(post_id: int, user_id: int) -> bool:
        """Delete a reaction."""
        conn = get_users_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM reactions WHERE post_id = ? AND user_id = ?",
                (post_id, user_id),
            )

            conn.commit()
            return True

        except Exception as e:
            logging.error(f"Error deleting reaction: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def get_by_user_and_post(user_id: int, post_id: int) -> Optional[Dict[str, Any]]:
        """Get a user's reaction to a post."""
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM reactions 
                WHERE user_id = ? AND post_id = ?
                """,
                (user_id, post_id),
            )

            reaction_data = cursor.fetchone()
            if reaction_data:
                return dict(reaction_data)
            return None

        except Exception as e:
            logging.error(f"Error getting reaction: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def count_by_post(post_id: int, reaction_type: Optional[str] = None) -> int:
        """Get the number of reactions for a post."""
        conn = get_users_db_connection()
        if not conn:
            return 0

        try:
            cursor = conn.cursor()
            if reaction_type:
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM reactions 
                    WHERE post_id = ? AND reaction_type = ?
                    """,
                    (post_id, reaction_type),
                )
            else:
                cursor.execute(
                    "SELECT COUNT(*) FROM reactions WHERE post_id = ?",
                    (post_id,),
                )

            return cursor.fetchone()[0]

        except Exception as e:
            logging.error(f"Error counting reactions: {e}")
            return 0
        finally:
            conn.close()

class Share:
    """Model for post shares."""

    @staticmethod
    def create(post_id: int, user_id: int) -> bool:
        """Create a new share."""
        conn = get_users_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO shares (post_id, user_id, created_at)
                VALUES (?, ?, datetime('now'))
                """,
                (post_id, user_id),
            )

            conn.commit()
            return True

        except Exception as e:
            logging.error(f"Error creating share: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @staticmethod
    def count_for_post(post_id: int) -> int:
        """Get the number of shares for a post."""
        conn = get_users_db_connection()
        if not conn:
            return 0

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM shares WHERE post_id = ?",
                (post_id,),
            )

            return cursor.fetchone()[0]

        except Exception as e:
            logging.error(f"Error counting shares: {e}")
            return 0
        finally:
            conn.close() 