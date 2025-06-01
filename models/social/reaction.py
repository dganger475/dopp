"""
Reaction model for handling post reactions.
"""

from utils.database import get_db_connection
from datetime import datetime

class Reaction:
    def __init__(self, id, post_id, user_id, reaction_type, created_at):
        self.id = id
        self.post_id = post_id
        self.user_id = user_id
        self.reaction_type = reaction_type
        self.created_at = created_at

    @classmethod
    def create(cls, post_id, user_id, reaction_type):
        """Create a new reaction."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            now = datetime.utcnow()
            cursor.execute(
                '''
                INSERT INTO reactions (post_id, user_id, reaction_type, created_at)
                VALUES (?, ?, ?, ?)
                ''',
                (post_id, user_id, reaction_type, now)
            )
            conn.commit()
            return cls(
                id=cursor.lastrowid,
                post_id=post_id,
                user_id=user_id,
                reaction_type=reaction_type,
                created_at=now
            )
        finally:
            conn.close()

    @classmethod
    def get_by_id(cls, id):
        """Get a reaction by ID."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM reactions WHERE id = ?',
                (id,)
            )
            row = cursor.fetchone()
            if row:
                return cls(
                    id=row[0],
                    post_id=row[1],
                    user_id=row[2],
                    reaction_type=row[3],
                    created_at=row[4]
                )
            return None
        finally:
            conn.close()

    @classmethod
    def get_by_post_id(cls, post_id):
        """Get all reactions for a post."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM reactions WHERE post_id = ? ORDER BY created_at DESC',
                (post_id,)
            )
            return [
                cls(
                    id=row[0],
                    post_id=row[1],
                    user_id=row[2],
                    reaction_type=row[3],
                    created_at=row[4]
                )
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()

    @classmethod
    def get_by_user_id(cls, user_id):
        """Get all reactions by a user."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM reactions WHERE user_id = ? ORDER BY created_at DESC',
                (user_id,)
            )
            return [
                cls(
                    id=row[0],
                    post_id=row[1],
                    user_id=row[2],
                    reaction_type=row[3],
                    created_at=row[4]
                )
                for row in cursor.fetchall()
            ]
        finally:
            conn.close()

    @classmethod
    def get_reaction_count(cls, post_id, reaction_type=None):
        """Get the count of reactions for a post."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            if reaction_type:
                cursor.execute(
                    'SELECT COUNT(*) FROM reactions WHERE post_id = ? AND reaction_type = ?',
                    (post_id, reaction_type)
                )
            else:
                cursor.execute(
                    'SELECT COUNT(*) FROM reactions WHERE post_id = ?',
                    (post_id,)
                )
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def delete(self):
        """Delete a reaction."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM reactions WHERE id = ?', (self.id,))
            conn.commit()
            return True
        finally:
            conn.close()

    def to_dict(self):
        """Convert the reaction to a dictionary."""
        return {
            'id': self.id,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'reaction_type': self.reaction_type,
            'created_at': self.created_at.isoformat()
        } 