"""
User Model
==========

Defines the User data model for user accounts, authentication, and profile data.
Includes relationships to faces, matches, notifications, and user utility functions.
"""

import logging
import sqlite3
from datetime import datetime
import os
from flask import current_app, url_for
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from utils.db.database import get_users_db_connection

# Configure logging
logger = logging.getLogger(__name__)

class User(UserMixin):
    """User model for authentication and profile management."""

    def __init__(
        self, id=None, username=None, email=None, password_hash=None, **kwargs
    ):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.first_name = kwargs.get("first_name", "")
        self.last_name = kwargs.get("last_name", "")
        self.bio = kwargs.get("bio", "")
        self.hometown = kwargs.get("hometown", "")
        self.current_location_city = kwargs.get("current_location_city", "")
        self.current_location_state = kwargs.get("current_location_state", "")
        self.birthdate = kwargs.get("birthdate", None)
        self.website = kwargs.get("website", "")
        self.interests = kwargs.get("interests", "")
        self.profile_image = kwargs.get(
            "profile_image", current_app.config["DEFAULT_PROFILE_IMAGE"]
        )
        self.cover_photo = kwargs.get(
            "cover_photo", current_app.config["DEFAULT_COVER_IMAGE"]
        )
        self.face_filename = kwargs.get("face_filename", None)
        self.profile_visibility = kwargs.get("profile_visibility", "public")
        self.share_real_name = kwargs.get("share_real_name", 0)
        self.share_location = kwargs.get("share_location", 0)
        self.share_age = kwargs.get("share_age", 0)
        self.created_at = kwargs.get(
            "created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_profile_image_url(self):
        """Return the URL for the user's profile image."""
        from flask import url_for, current_app

        if not self.profile_image or self.profile_image == "None":
            default_image_filename = current_app.config.get("DEFAULT_PROFILE_IMAGE")

            if not default_image_filename:
                # Fallback if config key is missing entirely
                default_image_filename = "images/default_profile.png"
            elif default_image_filename == "default_profile.png":
                # Correct the path if the config has the simple name without 'images/' prefix
                default_image_filename = "images/default_profile.png"
            # If default_image_filename is already "images/default_profile.png", or some other custom path
            # from config, it will be used as is.

            return url_for("static", filename=default_image_filename)

        # If already a full URL
        if self.profile_image.startswith(("http://", "https://")):
            return self.profile_image

        # If already an absolute static path
        if self.profile_image.startswith("/static/"):
            return self.profile_image

        # If a relative path like 'profile_pics/filename.png' or 'profile_images/filename.png'
        if "/" in self.profile_image:
            return url_for("static", filename=self.profile_image)

        # Otherwise, assume it's just a filename in profile_pics
        return url_for("static", filename=f"profile_pics/{self.profile_image}")

    @property
    def cover_photo_url(self):
        default_image_filename = current_app.config.get(
            "DEFAULT_COVER_IMAGE", "images/default_cover.png"
        )
        if not self.cover_photo or self.cover_photo == "None" or self.cover_photo.strip() == "":
            return url_for("static", filename=default_image_filename)
        # Use 'cover_photos/' to match the save location in routes/profile.py
        return url_for("static", filename=f'cover_photos/{self.cover_photo}')

    def get_id(self):
        return str(self.id)

    @classmethod
    def get_by_id(cls, user_id):
        """Get a user by their ID."""
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user_data = cursor.fetchone()

            if user_data:
                return cls(**dict(user_data))
            return None

        except Exception as e:
            logging.error(f"Error fetching user by id: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def get_by_username(cls, username):
        """Get a user by their username."""
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            user_data = cursor.fetchone()

            if user_data:
                return cls(**dict(user_data))
            return None

        except Exception as e:
            logging.error(f"Error fetching user by username: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def get_by_email(cls, email):
        """Get a user by their email."""
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            user_data = cursor.fetchone()

            if user_data:
                return cls(**dict(user_data))
            return None

        except Exception as e:
            logging.error(f"Error fetching user by email: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def create(username, email, password, **kwargs):
        """
        Create a new user.

        Args:
            username: Username for the new user
            email: Email address
            password: Plain text password (will be hashed)
            **kwargs: Additional user attributes

        Returns:
            User object if creation successful, None otherwise
        """
        conn = get_users_db_connection()
        if not conn:
            logger.error(f"[User.create] Failed to get DB connection!")
            return None

        try:
            cursor = conn.cursor()

            # Check if username or email already exists
            cursor.execute(
                "SELECT id FROM users WHERE username = ? OR email = ?",
                (username, email),
            )
            if cursor.fetchone():
                logger.warning(f"[User.create] Username or email already exists: username={username}, email={email}")
                return None  # Username or email already exists

            # Create password hash
            password_hash = generate_password_hash(password)

            # Set default profile image if not provided
            if "profile_image" not in kwargs:
                kwargs["profile_image"] = current_app.config["DEFAULT_PROFILE_IMAGE"]

            # Prepare the SQL statement with dynamic columns
            # Add face_filename if not present
            if "face_filename" not in kwargs:
                kwargs["face_filename"] = None
            columns = ["username", "email", "password_hash"] + list(kwargs.keys())
            placeholders = ["?"] * (len(columns))
            values = [username, email, password_hash] + list(kwargs.values())

            query = f"INSERT INTO users ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            cursor.execute(query, values)
            conn.commit()

            # Get the new user's ID
            user_id = cursor.lastrowid

            # Return the new user
            return User.get_by_id(user_id)

        except Exception as e:
            import traceback
            logger.error(f"Error creating user: {e}\nTraceback: {traceback.format_exc()}")
            try:
                logger.error(f"Last attempted SQL: {query} | Values: {values}")
            except Exception:
                pass
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    def verify_password(self, password):
        """Verify a password against the stored hash."""
        if not self.password_hash:
            logging.warning("[DEBUG] Password hash is missing for user: %s", self.username)
            return False
        
        logging.info(f"[DEBUG] Attempting to verify password for user: {self.username}")
        logging.info(f"[DEBUG] Stored password hash: {self.password_hash}")
        
        try:
            result = check_password_hash(self.password_hash, password)
            if not result:
                logging.warning(f"[DEBUG] Password verification failed for user: {self.username}")
            else:
                logging.info(f"[DEBUG] Password verification successful for user: {self.username}")
            return result
        except Exception as e:
            logging.error(f"[DEBUG] Error verifying password: {str(e)}")
            logging.error(f"[DEBUG] Exception type: {type(e).__name__}")
            return False

    def update(self, **kwargs):
        """
        Update user profile information. You can update face_filename, profile_image, etc.
        """
        if not self.id:
            return False

        conn = get_users_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            # Log what we're trying to update
            logging.info(f"Updating user {self.id} with attributes: {kwargs}")

            # Get the columns that actually exist in the users table
            cursor.execute("PRAGMA table_info(users)")
            existing_columns = [col[1] for col in cursor.fetchall()]

            # Log the available columns
            logging.info(f"Available columns in users table: {existing_columns}")

            # Ensure specific fields are properly handled
            critical_fields = [
                "first_name",
                "last_name",
                "birthdate",
                "hometown",
                "current_location_city",
                "current_location_state",
            ]
            for field in critical_fields:
                if field in kwargs:
                    # Explicitly log these critical fields
                    logging.info(
                        f"Critical field {field} value to update: '{kwargs[field]}'"
                    )
                    # Ensure empty strings are stored as empty strings, not NULL
                    if kwargs[field] is None:
                        kwargs[field] = ""

            # Filter out kwargs that don't match existing columns
            valid_updates = {k: v for k, v in kwargs.items() if k in existing_columns}

            # Log the valid updates we'll make
            logging.info(f"Valid updates to make: {valid_updates}")

            # Prepare the SQL statement with dynamic columns
            if not valid_updates:
                logging.warning("No valid updates found - check column names")
                return True  # Nothing to update

            # Construct query with explicit column names for clarity
            set_clauses = []
            values = []

            for key, value in valid_updates.items():
                set_clauses.append(f"{key} = ?")
                values.append(value)

            set_clause = ", ".join(set_clauses)
            values.append(self.id)  # Add ID for WHERE clause

            query = f"UPDATE users SET {set_clause} WHERE id = ?"
            logging.info(f"Executing update query: {query} with values: {values}")

            try:
                cursor.execute(query, values)
                conn.commit()

                # After update, query the database to confirm values were updated
                cursor.execute("SELECT * FROM users WHERE id = ?", (self.id,))
                updated_user = cursor.fetchone()

                if updated_user:
                    updated_dict = dict(updated_user)
                    logging.info(f"User after update: {updated_dict}")

                    # Verify critical fields were updated correctly
                    verification_failed = False
                    critical_fields = [
                        "first_name",
                        "last_name",
                        "birthdate",
                        "hometown",
                        "current_location_city",
                        "current_location_state",
                    ]

                    for field in critical_fields:
                        if field in valid_updates:
                            expected_value = valid_updates[field]
                            actual_value = updated_dict.get(field)

                            logging.info(
                                f"Verifying {field}: expected='{expected_value}', actual='{actual_value}'"
                            )

                            # Check if the update was successful
                            if expected_value != actual_value:
                                verification_failed = True
                                logging.error(
                                    f"Field {field} not updated correctly: expected '{expected_value}', got '{actual_value}'"
                                )

                    if verification_failed:
                        logging.warning(
                            "Some critical fields were not updated correctly"
                        )
                else:
                    logging.warning(f"Could not fetch updated user with ID {self.id}")
            except sqlite3.Error as sql_error:
                logging.error(f"SQL error during update: {sql_error}")
                conn.rollback()  # Explicitly rollback on SQL error
                raise

            # Update object attributes (including the invalid ones for the model)
            for key, value in kwargs.items():
                setattr(self, key, value)

            # Log successful update
            logging.info(f"Successfully updated user {self.id}")
            return True

        except Exception as e:
            logging.error(f"Error updating user: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def delete(self):
        """
        Delete the user from the database.

        Returns:
            True if deletion successful, False otherwise
        """
        if not self.id:
            return False

        conn = get_users_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            # Delete user's posts, comments, likes, and follows
            cursor.execute("DELETE FROM likes WHERE user_id = ?", (self.id,))
            cursor.execute("DELETE FROM comments WHERE user_id = ?", (self.id,))
            cursor.execute("DELETE FROM posts WHERE user_id = ?", (self.id,))
            cursor.execute(
                "DELETE FROM follows WHERE follower_id = ? OR followed_id = ?",
                (self.id, self.id),
            )
            cursor.execute("DELETE FROM claimed_profiles WHERE user_id = ?", (self.id,))

            # Finally delete the user
            cursor.execute("DELETE FROM users WHERE id = ?", (self.id,))
            conn.commit()

            return True

        except Exception as e:
            logging.error(f"Error deleting user: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def get_claimed_profiles(self):
        """
        Get profiles claimed by this user.

        Returns:
            List of claimed profile dictionaries
        """
        if not self.id:
            return []

        conn = get_users_db_connection()
        face_conn = get_users_db_connection(current_app.config["DB_PATH"])

        if not conn or not face_conn:
            return []

        try:
            cursor = conn.cursor()
            face_cursor = face_conn.cursor()

            cursor.execute(
                """
                SELECT * FROM claimed_profiles WHERE user_id = ? ORDER BY claimed_at DESC
            """,
                (self.id,),
            )

            claimed_profiles = []
            for profile in cursor.fetchall():
                profile_dict = dict(profile)

                # Get face data
                face_cursor.execute(
                    """
                    SELECT * FROM faces WHERE filename = ?
                """,
                    (profile_dict["face_filename"],),
                )

                face_data = face_cursor.fetchone()
                if face_data:
                    profile_dict["face_data"] = dict(face_data)

                claimed_profiles.append(profile_dict)

            return claimed_profiles

        except Exception as e:
            logging.error(f"Error fetching claimed profiles: {e}")
            return []
        finally:
            if conn:
                conn.close()
            if face_conn:
                face_conn.close()

    def get_followers(self):
        """
        Get users who follow this user.

        Returns:
            List of User objects
        """
        if not self.id:
            return []

        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT users.* FROM users
                JOIN follows ON users.id = follows.follower_id
                WHERE follows.followed_id = ?
            """,
                (self.id,),
            )

            followers = []
            for user_data in cursor.fetchall():
                followers.append(User(**dict(user_data)))

            return followers

        except Exception as e:
            logging.error(f"Error fetching followers: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_following(self):
        """
        Get users that this user follows.

        Returns:
            List of User objects
        """
        if not self.id:
            return []

        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT users.* FROM users
                JOIN follows ON users.id = follows.followed_id
                WHERE follows.follower_id = ?
            """,
                (self.id,),
            )

            following = []
            for user_data in cursor.fetchall():
                following.append(User(**dict(user_data)))

            return following

        except Exception as e:
            logging.error(f"Error fetching following: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def follow(self, user_id):
        """
        Follow another user.

        Args:
            user_id: ID of the user to follow

        Returns:
            True if successful, False otherwise
        """
        if not self.id or self.id == user_id:
            return False

        conn = get_users_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            # Check if already following
            cursor.execute(
                """
                SELECT id FROM follows 
                WHERE follower_id = ? AND followed_id = ?
            """,
                (self.id, user_id),
            )

            if cursor.fetchone():
                return True  # Already following

            # Add follow relationship
            cursor.execute(
                """
                INSERT INTO follows (follower_id, followed_id)
                VALUES (?, ?)
            """,
                (self.id, user_id),
            )

            conn.commit()
            return True

        except Exception as e:
            logging.error(f"Error following user: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    @classmethod
    def get_friend_suggestions(cls, user_id, limit=5):
        """
        Get friend suggestions for a user.

        This method suggests users to follow based on several criteria:
        1. Users followed by people the current user follows (friends of friends)
        2. Users with similar interests or locations
        3. Random active users if needed to fill the quota

        Args:
            user_id: ID of the user to get suggestions for
            limit: Maximum number of suggestions to return

        Returns:
            List of User objects representing suggested friends
        """
        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()

            # Get users that the user already follows
            cursor.execute(
                """
                SELECT followed_id FROM follows
                WHERE follower_id = ?
            """,
                (user_id,),
            )

            followed_ids = [row[0] for row in cursor.fetchall()]
            followed_ids.append(
                user_id
            )  # Add the user's own ID to exclude from suggestions

            # Convert list to string for SQL IN clause
            excluded_ids = ",".join(["?"] * len(followed_ids))

            # First priority: Friends of friends (users followed by people the user follows)
            cursor.execute(
                f"""
                SELECT DISTINCT u.* FROM users u
                JOIN follows f1 ON u.id = f1.followed_id
                JOIN follows f2 ON f1.follower_id = f2.followed_id
                WHERE f2.follower_id = ?
                AND u.id NOT IN ({excluded_ids})
                LIMIT ?
            """,
                [user_id] + followed_ids + [limit],
            )

            suggestions = []
            for user_data in cursor.fetchall():
                suggestions.append(cls(**dict(user_data)))

            # If we need more suggestions, add users with similar locations
            if len(suggestions) < limit:
                remaining = limit - len(suggestions)

                # Get the user's location
                cursor.execute(
                    "SELECT current_location_city, current_location_state FROM users WHERE id = ?",
                    (user_id,),
                )
                user_data = cursor.fetchone()

                if user_data and (
                    user_data["current_location_city"] or user_data["current_location_state"]
                ):
                    location_conditions = []
                    params = []

                    if user_data["current_location_city"]:
                        location_conditions.append("current_location_city = ?")
                        params.append(user_data["current_location_city"])

                    if user_data["current_location_state"]:
                        location_conditions.append("current_location_state = ?")
                        params.append(user_data["current_location_state"])

                    # Update excluded_ids to also exclude users we've already selected
                    suggestion_ids = [s.id for s in suggestions]
                    all_excluded = followed_ids + suggestion_ids
                    excluded_str = ",".join(["?"] * len(all_excluded))

                    cursor.execute(
                        f"""
                        SELECT * FROM users
                        WHERE ({' OR '.join(location_conditions)})
                        AND id NOT IN ({excluded_str})
                        ORDER BY RANDOM()
                        LIMIT ?
                    """,
                        params + all_excluded + [remaining],
                    )

                    for user_data in cursor.fetchall():
                        suggestions.append(cls(**dict(user_data)))

            # If we still need more, add some random active users
            if len(suggestions) < limit:
                remaining = limit - len(suggestions)

                # Update excluded_ids again
                suggestion_ids = [s.id for s in suggestions]
                all_excluded = followed_ids + suggestion_ids
                excluded_str = ",".join(["?"] * len(all_excluded))

                cursor.execute(
                    f"""
                    SELECT * FROM users
                    WHERE id NOT IN ({excluded_str})
                    ORDER BY RANDOM()
                    LIMIT ?
                """,
                    all_excluded + [remaining],
                )

                for user_data in cursor.fetchall():
                    suggestions.append(cls(**dict(user_data)))

            return suggestions

        except Exception as e:
            logging.error(f"Error getting friend suggestions: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def unfollow(self, user_id):
        """
        Unfollow a user.

        Args:
            user_id: ID of the user to unfollow

        Returns:
            True if successful, False otherwise
        """
        if not self.id:
            return False

        conn = get_users_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM follows 
                WHERE follower_id = ? AND followed_id = ?
            """,
                (self.id, user_id),
            )

            conn.commit()
            return True

        except Exception as e:
            logging.error(f"Error unfollowing user: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def is_following(self, user_id):
        """
        Check if this user is following another user.

        Args:
            user_id: ID of the user to check

        Returns:
            True if following, False otherwise
        """
        if not self.id:
            return False

        conn = get_users_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id FROM follows 
                WHERE follower_id = ? AND followed_id = ?
            """,
                (self.id, user_id),
            )

            return cursor.fetchone() is not None

        except Exception as e:
            logging.error(f"Error checking follow status: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_follower_count(self):
        """
        Get the count of followers for this user.

        Returns:
            int: Number of followers
        """
        if not self.id:
            return 0

        conn = get_users_db_connection()
        if not conn:
            return 0

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT COUNT(*) as count FROM follows 
                WHERE followed_id = ?
            """,
                (self.id,),
            )

            result = cursor.fetchone()
            return result["count"] if result else 0

        except Exception as e:
            logging.error(f"Error counting followers: {e}")
            return 0
        finally:
            if conn:
                conn.close()

    def to_dict(self, include_private=False):
        """
        Convert user to dictionary, respecting privacy settings.

        Args:
            include_private: Whether to include private information

        Returns:
            Dictionary with user data
        """
        data = {
            "id": self.id,
            "username": self.username,
            "bio": self.bio,
            "profile_image": self.profile_image,
            "created_at": self.created_at,
        }

        # Only include these if they're shared or we're including private data
        if include_private or self.share_real_name:
            data["first_name"] = self.first_name
            data["last_name"] = self.last_name

        if include_private or self.share_location:
            data["hometown"] = self.hometown
            data["current_location_city"] = self.current_location_city
            data["current_location_state"] = self.current_location_state

        if include_private or self.share_age:
            data["birthdate"] = self.birthdate

        if include_private:
            data["email"] = self.email
            data["website"] = self.website
            data["interests"] = self.interests
            data["profile_visibility"] = self.profile_visibility
            data["cover_photo"] = self.cover_photo

        return data
