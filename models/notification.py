import logging

"""
Notification Model
==================

Defines the Notification data model for user and system notifications.
Includes logic for notification creation, retrieval, and status updates.
"""
from datetime import datetime

from utils.db.database import get_users_db_connection


class Notification:
    """Model for handling user notifications."""

    TYPE_MATCH_CLAIMED = "match_claimed"
    TYPE_CONNECTION_REQUEST = "connection_request"
    TYPE_NEW_FOLLOWER = "new_follower"
    TYPE_COMMENT = "comment"
    TYPE_LIKE = "like"
    TYPE_SYSTEM = "system"

    def __init__(self, id=None, user_id=None, type=None, **kwargs):
        self.id = id
        self.user_id = user_id
        self.type = type
        self.content = kwargs.get("content", "")
        self.entity_id = kwargs.get("entity_id", None)
        self.entity_type = kwargs.get("entity_type", None)
        self.sender_id = kwargs.get("sender_id", None)
        self.is_read = kwargs.get("is_read", 0)
        self.created_at = kwargs.get(
            "created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self._sender = None  # Cached sender object

    @classmethod
    def setup_table(cls):
        """Create notifications table if it doesn't exist."""
        conn = get_users_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            # Create notifications table
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                content TEXT,
                entity_id TEXT,
                entity_type TEXT,
                sender_id INTEGER,
                is_read INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (sender_id) REFERENCES users(id)
            )
            """
            )

            conn.commit()
            return True

        except Exception as e:
            logging.error(f"Error setting up notifications table: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @classmethod
    def get_by_id(cls, notification_id):
        """Get a notification by its ID."""
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM notifications WHERE id = ?", (notification_id,)
            )
            notif_data = cursor.fetchone()

            if notif_data:
                return cls(**dict(notif_data))
            return None

        except Exception as e:
            logging.error(f"Error fetching notification by id: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def get_by_user_id(cls, user_id, limit=20, offset=0, unread_only=False):
        """Get notifications for a user.

        Args:
            user_id: The ID of the user
            limit: Maximum number of notifications to return
            offset: Offset for pagination
            unread_only: If True, only return unread notifications

        Returns:
            List of Notification objects
        """
        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()

            query = "SELECT * FROM notifications WHERE user_id = ?"
            params = [user_id]

            if unread_only:
                query += " AND is_read = 0"

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)

            notifications = []
            for notif_data in cursor.fetchall():
                notifications.append(cls(**dict(notif_data)))

            return notifications

        except Exception as e:
            logging.error(f"Error fetching notifications for user: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    def create(cls, user_id, type, **kwargs):
        """Create a new notification.

        Args:
            user_id: ID of the user to receive the notification
            type: Type of notification
            **kwargs: Additional notification attributes

        Returns:
            Notification object if successful, None otherwise
        """
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()

            # Prepare the SQL statement with dynamic columns
            columns = ["user_id", "type"] + list(kwargs.keys())
            placeholders = ["?"] * len(columns)
            values = [user_id, type] + list(kwargs.values())

            query = f"INSERT INTO notifications ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            cursor.execute(query, values)
            conn.commit()

            # Get the new notification's ID
            notif_id = cursor.lastrowid

            # Return the new notification
            return Notification.get_by_id(notif_id)

        except Exception as e:
            logging.error(f"Error creating notification: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    @classmethod
    def notify_match_claimed(cls, match_filename, claimer_id, claimed_profile_id):
        """Create notifications for users who have added this match to their profile.

        Args:
            match_filename: Filename of the match that was claimed
            claimer_id: ID of the user who claimed the match
            claimed_profile_id: ID of the claimed profile

        Returns:
            Number of notifications created
        """
        from models.user_match import UserMatch

        conn = get_users_db_connection()
        if not conn:
            return 0

        try:
            cursor = conn.cursor()

            # Find users who have added this match to their profile
            cursor.execute(
                """
                SELECT user_id FROM user_matches
                WHERE match_filename = ? AND user_id != ?
            """,
                (match_filename, claimer_id),
            )

            count = 0
            for row in cursor.fetchall():
                user_id = row[0]

                # Create a notification for this user
                notification = cls.create(
                    user_id=user_id,
                    type=cls.TYPE_MATCH_CLAIMED,
                    content=f"A match you added to your profile has been claimed!",
                    entity_id=str(claimed_profile_id),
                    entity_type="claimed_profile",
                    sender_id=claimer_id,
                )

                if notification:
                    count += 1

            return count

        except Exception as e:
            logging.error(f"Error creating match claimed notifications: {e}")
            return 0
        finally:
            if conn:
                conn.close()

    def mark_as_read(self):
        """Mark this notification as read."""
        if not self.id:
            return False

        conn = get_users_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE notifications SET is_read = 1 WHERE id = ?", (self.id,)
            )
            conn.commit()

            self.is_read = 1
            return True

        except Exception as e:
            logging.error(f"Error marking notification as read: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @classmethod
    def mark_all_as_read(cls, user_id):
        """Mark all notifications for a user as read.

        Args:
            user_id: The ID of the user

        Returns:
            Number of notifications marked as read
        """
        conn = get_users_db_connection()
        if not conn:
            return 0

        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
                (user_id,),
            )
            conn.commit()

            return cursor.rowcount

        except Exception as e:
            logging.error(f"Error marking all notifications as read: {e}")
            if conn:
                conn.rollback()
            return 0
        finally:
            if conn:
                conn.close()

    # Method removed - duplicate implementation

    @classmethod
    def count_unread(cls, user_id):
        """Count unread notifications for a user."""
        conn = get_users_db_connection()
        if not conn:
            return 0

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0",
                (user_id,),
            )
            result = cursor.fetchone()

            if result:
                return result[0]
            return 0

        except Exception as e:
            logging.error(f"Error counting unread notifications: {e}")
            return 0
        finally:
            conn.close()
