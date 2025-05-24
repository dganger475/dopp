"""
Reaction Model
=============

Handles reactions on posts (like, amazing, related, wow).
"""

import logging
from datetime import datetime

from models.user import User
from utils.db.database import get_users_db_connection


class Reaction:
    """Model for handling post reactions."""

    TYPES = ["like", "amazing", "related", "wow"]

    def __init__(
        self, id=None, user_id=None, post_id=None, reaction_type=None, **kwargs
    ):
        self.id = id
        self.user_id = user_id
        self.post_id = post_id
        self.reaction_type = reaction_type
        self.created_at = kwargs.get(
            "created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self._user = None

    @classmethod
    def get_by_id(cls, reaction_id):
        """Get a reaction by its ID."""
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, user_id, post_id, reaction_type, created_at 
                FROM reactions 
                WHERE id = ?
            """,
                (reaction_id,),
            )
            data = cursor.fetchone()

            if data:
                return cls(**dict(data))
            return None

        except Exception as e:
            logging.error(f"Error fetching reaction: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def get_by_user_and_post(cls, user_id, post_id):
        """Get a user's reaction on a post."""
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, user_id, post_id, reaction_type, created_at 
                FROM reactions 
                WHERE user_id = ? AND post_id = ?
            """,
                (user_id, post_id),
            )
            data = cursor.fetchone()

            if data:
                return cls(**dict(data))
            return None

        except Exception as e:
            logging.error(f"Error fetching reaction: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def count_by_post(cls, post_id, reaction_type=None):
        """Count reactions on a post, optionally filtered by type."""
        conn = get_users_db_connection()
        if not conn:
            return 0

        try:
            cursor = conn.cursor()

            # First check if reactions table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='reactions'"
            )
            if not cursor.fetchone():
                return 0

            # Now count reactions
            if reaction_type:
                cursor.execute(
                    """
                    SELECT COUNT(*) 
                    FROM reactions 
                    WHERE post_id = ? AND reaction_type = ?
                """,
                    (post_id, reaction_type),
                )
            else:
                cursor.execute(
                    """
                    SELECT COUNT(*) 
                    FROM reactions 
                    WHERE post_id = ?
                """,
                    (post_id,),
                )
            return cursor.fetchone()[0]

        except Exception as e:
            logging.error(f"Error counting reactions: {e}")
            return 0
            return 0
        finally:
            conn.close()

    @classmethod
    def create(cls, user_id, post_id, reaction_type):
        """Create or update a reaction."""
        if reaction_type not in cls.TYPES:
            return None

        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            # First try to update existing reaction
            cursor.execute(
                """
                UPDATE reactions 
                SET reaction_type = ? 
                WHERE user_id = ? AND post_id = ?
            """,
                (reaction_type, user_id, post_id),
            )

            if cursor.rowcount == 0:
                # No existing reaction, create new one
                cursor.execute(
                    """
                    INSERT INTO reactions (user_id, post_id, reaction_type)
                    VALUES (?, ?, ?)
                """,
                    (user_id, post_id, reaction_type),
                )

            conn.commit()
            return cls.get_by_user_and_post(user_id, post_id)

        except Exception as e:
            logging.error(f"Error creating reaction: {e}")
            return None
        finally:
            conn.close()

    def delete(self):
        """Delete the reaction."""
        conn = get_users_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reactions WHERE id = ?", (self.id,))
            conn.commit()
            return True

        except Exception as e:
            logging.error(f"Error deleting reaction: {e}")
            return False
        finally:
            conn.close()

    def get_user(self):
        """Get the user who created this reaction."""
        if not self._user and self.user_id:
            self._user = User.get_by_id(self.user_id)
        return self._user

    def to_dict(self, include_user=True):
        """Convert reaction to dictionary."""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "post_id": self.post_id,
            "reaction_type": self.reaction_type,
            "created_at": self.created_at,
        }

        if include_user:
            user = self.get_user()
            if user:
                data["user"] = user.to_dict()

        return data
