"""Notification Models
===================

Defines models for social media notifications and related operations.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from models.user import User
from utils.db.database import get_users_db_connection
from utils.database import get_db_connection

class Notification:
    """Model for user notifications."""

    def __init__(self, id=None, user_id=None, notification_type=None, content=None, created_at=None, read_at=None):
        self.id = id
        self.user_id = user_id
        self.notification_type = notification_type
        self.content = content
        self.created_at = created_at
        self.read_at = read_at

    @classmethod
    def get_for_user(cls, user_id: int, limit: int = 20, offset: int = 0) -> List['Notification']:
        """Get notifications for a user."""
        conn = get_users_db_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM notifications
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, limit, offset)
            )
            return [cls(**dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error fetching notifications: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    def create(cls, user_id: int, notification_type: str, content: str) -> Optional['Notification']:
        """Create a new notification."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            now = datetime.utcnow()
            cursor.execute(
                """
                INSERT INTO notifications (user_id, notification_type, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, notification_type, content, now)
            )
            conn.commit()
            return cls(
                id=cursor.lastrowid,
                user_id=user_id,
                notification_type=notification_type,
                content=content,
                created_at=now
            )
        except Exception as e:
            logging.error(f"Error creating notification: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            conn.close()

    @classmethod
    def get_by_id(cls, notification_id: int) -> Optional['Notification']:
        """Get a notification by its ID."""
        conn = get_db_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notifications WHERE id = ?", (notification_id,))
            row = cursor.fetchone()
            if row:
                return cls(
                    id=row[0],
                    user_id=row[1],
                    notification_type=row[2],
                    content=row[3],
                    created_at=row[4],
                    read_at=row[5]
                )
            return None
        except Exception as e:
            logging.error(f"Error fetching notification by id: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def get_by_user_id(cls, user_id: int, limit: int = 20, offset: int = 0) -> List['Notification']:
        """Get all notifications for a user."""
        conn = get_db_connection()
        if not conn:
            return []
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM notifications
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, limit, offset)
            )
            return [cls(**dict(row)) for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error fetching notifications: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    def get_unread_count(cls, user_id: int) -> int:
        """Get the count of unread notifications for a user."""
        conn = get_db_connection()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) FROM notifications
                WHERE user_id = ? AND read_at IS NULL
                """,
                (user_id,)
            )
            return cursor.fetchone()[0]
        except Exception as e:
            logging.error(f"Error fetching unread notification count: {e}")
            return 0
        finally:
            conn.close()

    def mark_as_read(self) -> bool:
        """Mark this notification as read."""
        if not self.id:
            return False
        conn = get_db_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            now = datetime.utcnow()
            cursor.execute(
                "UPDATE notifications SET read_at = ? WHERE id = ?",
                (now, self.id)
            )
            conn.commit()
            self.read_at = now
            return True
        except Exception as e:
            logging.error(f"Error marking notification as read: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            conn.close()

    def delete(self) -> bool:
        """Delete this notification."""
        if not self.id:
            return False
        conn = get_db_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM notifications WHERE id = ?", (self.id,))
            conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error deleting notification: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            conn.close()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "notification_type": self.notification_type,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "read_at": self.read_at.isoformat() if self.read_at else None
        } 