import logging
import sqlite3

from utils.db.database import get_users_db_connection


class Follow:
    """Model for user follows/followers relationships."""

    def __init__(self, id=None, follower_id=None, followed_id=None, created_at=None):
        self.id = id
        self.follower_id = follower_id
        self.followed_id = followed_id
        self.created_at = created_at

    @staticmethod
    def follow(follower_id, followed_id):
        """
        Create a new follow relationship.

        Args:
            follower_id: ID of the user doing the following
            followed_id: ID of the user being followed

        Returns:
            True if successful, False otherwise
        """
        if follower_id == followed_id:
            return False  # Can't follow yourself

        conn = get_users_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            # Check if already following
            cursor.execute(
                "SELECT id FROM follows WHERE follower_id = ? AND followed_id = ?",
                (follower_id, followed_id),
            )

            if cursor.fetchone():
                return True  # Already following

            # Create new follow
            cursor.execute(
                "INSERT INTO follows (follower_id, followed_id) VALUES (?, ?)",
                (follower_id, followed_id),
            )

            conn.commit()
            return True

        except Exception as e:
            logging.error(f"Error creating follow: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def unfollow(follower_id, followed_id):
        """
        Remove a follow relationship.

        Args:
            follower_id: ID of the user doing the unfollowing
            followed_id: ID of the user being unfollowed

        Returns:
            True if successful, False otherwise
        """
        conn = get_users_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM follows WHERE follower_id = ? AND followed_id = ?",
                (follower_id, followed_id),
            )

            conn.commit()
            return True

        except Exception as e:
            logging.error(f"Error removing follow: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def is_following(follower_id, followed_id):
        """
        Check if one user is following another.

        Args:
            follower_id: ID of the user who might be following
            followed_id: ID of the user who might be followed

        Returns:
            True if following, False otherwise
        """
        conn = get_users_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id FROM follows WHERE follower_id = ? AND followed_id = ?",
                (follower_id, followed_id),
            )

            return cursor.fetchone() is not None

        except Exception as e:
            logging.error(f"Error checking follow status: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def get_followers(user_id):
        """
        Get all followers of a user.

        Args:
            user_id: The user to get followers for

        Returns:
            List of user IDs who follow the given user
        """
        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT follower_id FROM follows WHERE followed_id = ?", (user_id,)
            )

            return [row[0] for row in cursor.fetchall()]

        except Exception as e:
            logging.error(f"Error getting followers: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_following(user_id):
        """
        Get all users that a user is following.

        Args:
            user_id: The user to get following for

        Returns:
            List of user IDs the given user follows
        """
        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT followed_id FROM follows WHERE follower_id = ?", (user_id,)
            )

            return [row[0] for row in cursor.fetchall()]

        except Exception as e:
            logging.error(f"Error getting following: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_follower_count(user_id):
        """
        Get the count of followers for a user.

        Args:
            user_id: The user to get follower count for

        Returns:
            Number of followers
        """
        conn = get_users_db_connection()
        if not conn:
            return 0

        try:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT COUNT(*) FROM follows WHERE followed_id = ?", (user_id,)
            )

            return cursor.fetchone()[0]

        except Exception as e:
            logging.error(f"Error getting follower count: {e}")
            return 0
        finally:
            conn.close()

    @staticmethod
    def get_following_count(user_id):
        """
        Get the count of users a user is following.

        Args:
            user_id: The user to get following count for

        Returns:
            Number of users being followed
        """
        conn = get_users_db_connection()
        if not conn:
            return 0

        try:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT COUNT(*) FROM follows WHERE follower_id = ?", (user_id,)
            )

            return cursor.fetchone()[0]

        except Exception as e:
            logging.error(f"Error getting following count: {e}")
            return 0
        finally:
            conn.close()
