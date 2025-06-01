"""
ClaimedProfile model for handling claimed user profiles.
"""

from utils.db.database import get_db_connection
from datetime import datetime
import logging

class ClaimedProfile:
    def __init__(self, id, user_id, face_id, claimed_at, status, relationship=None, caption=None):
        self.id = id
        self.user_id = user_id
        self.face_id = face_id
        self.claimed_at = claimed_at
        self.status = status
        self.relationship = relationship
        self.caption = caption

    @classmethod
    def create(cls, user_id, face_id, face_filename, relationship=None, caption=None):
        """Create a new claimed profile."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    '''
                    INSERT INTO claimed_profiles (user_id, face_id, face_filename, relationship, caption, claimed_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (user_id, face_id, face_filename, relationship, caption, datetime.utcnow(), 'pending')
                )
                conn.commit()
                return cls(
                    id=cursor.lastrowid,
                    user_id=user_id,
                    face_id=face_id,
                    claimed_at=datetime.utcnow(),
                    status='pending',
                    relationship=relationship,
                    caption=caption
                )
        except Exception as e:
            logging.error(f"Error creating claimed profile: {e}")
            return None

    @classmethod
    def get_by_id(cls, id):
        """Get a claimed profile by ID."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM claimed_profiles WHERE id = ?',
                    (id,)
                )
                row = cursor.fetchone()
                if row:
                    return cls(
                        id=row[0],
                        user_id=row[1],
                        face_id=row[2],
                        relationship=row[3],
                        caption=row[4],
                        claimed_at=row[5],
                        status=row[6] if len(row) > 6 else 'pending'
                    )
                return None
        except Exception as e:
            logging.error(f"Error getting claimed profile by id: {e}")
            return None

    @classmethod
    def get_by_user_id(cls, user_id):
        """Get all claimed profiles for a user."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT * FROM claimed_profiles WHERE user_id = ?',
                    (user_id,)
                )
                return [
                    cls(
                        id=row[0],
                        user_id=row[1],
                        face_id=row[2],
                        relationship=row[3],
                        caption=row[4],
                        claimed_at=row[5],
                        status=row[6] if len(row) > 6 else 'pending'
                    )
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logging.error(f"Error getting claimed profiles by user_id: {e}")
            return []

    @classmethod
    def get_by_face_id(cls, face_id):
        """Get all claimed profiles for a face."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # First check if the face_id column exists
                cursor.execute("PRAGMA table_info(claimed_profiles)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'face_id' not in columns:
                    logging.warning("face_id column not found in claimed_profiles table")
                    return []
                
                cursor.execute(
                    'SELECT * FROM claimed_profiles WHERE face_id = ?',
                    (face_id,)
                )
                rows = cursor.fetchall()
                return [
                    cls(
                        id=row[0],
                        user_id=row[1],
                        face_id=row[2],
                        relationship=row[3],
                        caption=row[4],
                        claimed_at=row[5],
                        status=row[6] if len(row) > 6 else 'pending'
                    )
                    for row in rows
                ]
        except Exception as e:
            logging.error(f"Error getting claimed profiles by face_id: {e}")
            return []

    def update_status(self, status):
        """Update the status of a claimed profile."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'UPDATE claimed_profiles SET status = ? WHERE id = ?',
                    (status, self.id)
                )
                conn.commit()
                self.status = status
                return True
        except Exception as e:
            logging.error(f"Error updating claimed profile status: {e}")
            return False

    def delete(self):
        """Delete a claimed profile."""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM claimed_profiles WHERE id = ?', (self.id,))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error deleting claimed profile: {e}")
            return False

    def to_dict(self):
        """Convert the claimed profile to a dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'face_id': self.face_id,
            'relationship': self.relationship,
            'caption': self.caption,
            'claimed_at': self.claimed_at.isoformat() if hasattr(self.claimed_at, 'isoformat') else str(self.claimed_at),
            'status': self.status
        } 