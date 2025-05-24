"""
UserMatch Model
===============

Defines the UserMatch data model for tracking which historical matches are associated with which users.
Handles logic for adding, removing, and querying user matches.
"""

import logging
import random
from datetime import datetime

from flask import session

from models.face import Face
from models.social import ClaimedProfile
from utils.db.database import get_users_db_connection


class UserMatch:
    """Model for handling user-added matches and their visibility settings."""

    @classmethod
    def get_by_match_id(cls, match_id):
        """Get a match by its ID instead of filename for privacy."""
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_matches WHERE id = ?", (match_id,))
            match_data = cursor.fetchone()

            if match_data:
                return cls(**dict(match_data))
            return None

        except Exception as e:
            logging.error(f"Error fetching user match by match_id: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def __init__(
        self, id=None, user_id=None, match_filename=None, face_id=None, **kwargs
    ):
        self.id = id
        self.user_id = user_id
        self.match_filename = match_filename
        self.face_id = face_id
        self.is_visible = kwargs.get("is_visible", 1)
        self.privacy_level = kwargs.get("privacy_level", "public")
        self.similarity = kwargs.get("similarity", None)  # Similarity percentage
        self.added_at = kwargs.get(
            "added_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self._match_details = None  # Cached match details

    @classmethod
    def get_by_id(cls, match_id):
        """Get a user match by its ID."""
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_matches WHERE id = ?", (match_id,))
            match_data = cursor.fetchone()

            if match_data:
                return cls(**dict(match_data))
            return None

        except Exception as e:
            logging.error(f"Error fetching user match by id: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def get_by_user_and_filename(cls, user_id, match_filename):
        """Get a user match by user ID and match filename (legacy)."""
        conn = get_users_db_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM user_matches WHERE user_id = ? AND match_filename = ?",
                (user_id, match_filename),
            )
            match_data = cursor.fetchone()
            if match_data:
                return cls(**dict(match_data))
            return None
        except Exception as e:
            logging.error(f"Error fetching user match by user and filename: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def get_by_user_and_face_id(cls, user_id, face_id):
        """Get a user match by user ID and face_id (preferred)."""
        conn = get_users_db_connection()
        if not conn:
            return None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM user_matches WHERE user_id = ? AND face_id = ?",
                (user_id, face_id),
            )
            match_data = cursor.fetchone()
            if match_data:
                return cls(**dict(match_data))
            return None
        except Exception as e:
            logging.error(f"Error fetching user match by user and face_id: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def get_by_user_id(cls, user_id, visible_only=False, respect_privacy=True):
        """Get all matches added by a user.

        Args:
            user_id: The ID of the user
            visible_only: If True, only return matches marked as visible
            respect_privacy: If True, respect privacy settings for non-owners

        Returns:
            List of UserMatch objects
        """
        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            current_user_id = session.get("user_id")

            # If viewing own profile, show all matches regardless of privacy
            # Or if respect_privacy is False (admin/system view)
            if (
                current_user_id and int(current_user_id) == int(user_id)
            ) or not respect_privacy:
                if visible_only:
                    cursor.execute(
                        """
                        SELECT * FROM user_matches 
                        WHERE user_id = ? AND is_visible = 1
                        ORDER BY added_at DESC
                    """,
                        (user_id,),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM user_matches 
                        WHERE user_id = ?
                        ORDER BY added_at DESC
                    """,
                        (user_id,),
                    )
            else:
                # For other users viewing, respect privacy settings
                from models.user import User

                viewer = User.get_by_id(current_user_id) if current_user_id else None
                profile_owner = User.get_by_id(user_id)

                # Check friendship status
                is_friend = (
                    viewer
                    and profile_owner
                    and (
                        viewer.is_following(profile_owner.id)
                        or profile_owner.is_following(viewer.id)
                    )
                )

                if visible_only:
                    # Three privacy levels: public, friends, private
                    if is_friend:
                        # Friends can see public and friends-only matches
                        cursor.execute(
                            """
                            SELECT * FROM user_matches 
                            WHERE user_id = ? AND is_visible = 1 
                            AND (privacy_level = 'public' OR privacy_level = 'friends')
                            ORDER BY added_at DESC
                        """,
                            (user_id,),
                        )
                    else:
                        # Non-friends can only see public matches
                        cursor.execute(
                            """
                            SELECT * FROM user_matches 
                            WHERE user_id = ? AND is_visible = 1 AND privacy_level = 'public'
                            ORDER BY added_at DESC
                        """,
                            (user_id,),
                        )
                else:
                    # Same rules but including invisible matches (likely admin view)
                    if is_friend:
                        cursor.execute(
                            """
                            SELECT * FROM user_matches 
                            WHERE user_id = ? 
                            AND (privacy_level = 'public' OR privacy_level = 'friends')
                            ORDER BY added_at DESC
                        """,
                            (user_id,),
                        )
                    else:
                        cursor.execute(
                            """
                            SELECT * FROM user_matches 
                            WHERE user_id = ? AND privacy_level = 'public'
                            ORDER BY added_at DESC
                        """,
                            (user_id,),
                        )

            matches = []
            for match_data in cursor.fetchall():
                matches.append(cls(**dict(match_data)))

            return matches

        except Exception as e:
            logging.error(f"Error fetching user matches: {e}")
            return []
        finally:
            conn.close()
        return []

    @classmethod
    def add_match(
        cls,
        user_id,
        match_filename=None,
        face_id=None,
        is_visible=1,
        privacy_level="public",
        similarity=None,
    ):
        """Add a match to a user's profile, using face_id if available.
        Args:
            user_id: ID of the user
            match_filename: Filename of the match face (legacy, for backward compatibility)
            face_id: ID of the face (preferred)
            is_visible: Whether the match should be visible on the profile (1=yes, 0=no)
            privacy_level: Privacy level for the match (public, friends, private)
            similarity: Similarity score (optional)
        Returns:
            UserMatch object if successful, None otherwise
        """
        conn = get_users_db_connection()
        if not conn:
            return None
        # Prefer face_id for lookup
        existing = None
        if face_id is not None:
            existing = cls.get_by_user_and_face_id(user_id, face_id)
        if not existing and match_filename:
            existing = cls.get_by_user_and_filename(user_id, match_filename)
        if existing:
            # If already added but settings changed, update them
            updated = False
            if (
                existing.is_visible != is_visible
                or existing.privacy_level != privacy_level
            ):
                existing.update(is_visible=is_visible, privacy_level=privacy_level)
                updated = True
            if similarity is not None and existing.similarity != similarity:
                existing.update(similarity=similarity)
                updated = True
            if updated:
                logging.info(
                    f"Updated existing UserMatch id={existing.id} for user_id={user_id}, face_id={face_id}"
                )
            return existing
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO user_matches 
                (user_id, match_filename, face_id, is_visible, privacy_level, similarity, added_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    match_filename,
                    face_id,
                    is_visible,
                    privacy_level,
                    similarity,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            conn.commit()
            match_id = cursor.lastrowid
            return UserMatch.get_by_id(match_id)
        except Exception as e:
            logging.error(f"Error adding match to profile: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    @classmethod
    def remove_match(cls, user_id, match_filename):
        """Remove a match from a user's profile.

        Args:
            user_id: ID of the user
            match_filename: Filename of the match to remove

        Returns:
            True if successful, False otherwise
        """
        conn = get_users_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM user_matches 
                WHERE user_id = ? AND match_filename = ?
            """,
                (user_id, match_filename),
            )

            conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            logging.error(f"Error removing match from profile: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def update(self, **kwargs):
        """Update user match attributes."""
        if not self.id:
            return False

        conn = get_users_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            update_fields = []
            values = []

            for key, value in kwargs.items():
                if hasattr(self, key):
                    update_fields.append(f"{key} = ?")
                    values.append(value)
                    setattr(self, key, value)

            if not update_fields:
                return True

            values.append(self.id)

            cursor.execute(
                f"""
                UPDATE user_matches
                SET {', '.join(update_fields)}
                WHERE id = ?
            """,
                values,
            )

            conn.commit()
            return True

        except Exception as e:
            logging.error(f"Error updating user match: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def toggle_visibility(self):
        """Toggle the visibility of this match on the user's profile."""
        new_visibility = 0 if self.is_visible else 1
        success = self.update(is_visible=new_visibility)
        if success:
            self.is_visible = new_visibility
        return success

    def set_privacy(self, privacy_level):
        """Set the privacy level for this match.

        Args:
            privacy_level: One of 'public', 'friends', or 'private'

        Returns:
            True if successful, False otherwise
        """
        if privacy_level not in ("public", "friends", "private"):
            return False

        success = self.update(privacy_level=privacy_level)
        if success:
            self.privacy_level = privacy_level
        return success

    @classmethod
    def get_privacy_levels(cls):
        """Get the list of available privacy levels.

        Returns:
            Dictionary of privacy levels and their user-friendly descriptions
        """
        return {
            "public": "Visible to everyone",
            "friends": "Visible only to friends",
            "private": "Visible only to you",
        }

    def can_view(self, viewer_id=None):
        """Check if a user can view this match based on privacy settings.

        Args:
            viewer_id: ID of the user trying to view the match (None for anonymous)

        Returns:
            True if the user can view this match, False otherwise
        """
        # Owner can always view their own matches
        if viewer_id and int(viewer_id) == int(self.user_id):
            return True

        # Must be visible to be viewable
        if not self.is_visible:
            return False

        # Check privacy level
        if self.privacy_level == "public":
            return True
        elif self.privacy_level == "private":
            return False  # Only owner can see private matches
        elif self.privacy_level == "friends":
            # Check if viewer is a friend
            if not viewer_id:
                return False  # Anonymous users cannot be friends

            from models.user import User

            user = User.get_by_id(self.user_id)
            viewer = User.get_by_id(viewer_id)

            if not user or not viewer:
                return False

            # Either direction of following counts as friends
            return user.is_following(viewer.id) or viewer.is_following(user.id)

    def get_match_details(self):
        """Get the face details for this match."""
        if self._match_details is None:
            from models.face import Face

            # Look for claimed profile first
            claimed = ClaimedProfile.get_by_filename(self.match_filename)
            if claimed:
                # Include limited metadata (decade and state)
                face = Face.get_by_filename(self.match_filename)
                from utils.face.metadata import get_metadata_for_face

                metadata = (
                    get_metadata_for_face(face)
                    if face
                    else {"decade": "Unknown", "state": "Unknown"}
                )
                self._match_details = {
                    "filename": self.match_filename,
                    "is_claimed": True,
                    "decade": metadata.get("decade", "Unknown"),
                    "state": metadata.get("state", "Unknown"),
                    "similarity": self.similarity,  # Use actual stored similarity
                    # Retain relationship info internally but not necessarily shown in UI
                    "relationship": claimed.relationship,
                    "caption": claimed.caption,
                    "user_id": claimed.user_id,
                }
            else:
                # Get raw face data
                face = Face.get_by_filename(self.match_filename)
                if face:
                    from utils.face.metadata import get_metadata_for_face

                    metadata = get_metadata_for_face(face)
                    # Extract metadata from filename if it's unknown
                    decade = metadata.get("decade", "Unknown")
                    state = metadata.get("state", "Unknown")

                    # Apply fallback logic for decade if it's unknown
                    if decade == "Unknown" and self.match_filename:
                        import re

                        # Try to extract decade from filename
                        decade_match = re.search(
                            r"((?:19|20)\d0)s", self.match_filename
                        )
                        if decade_match:
                            decade = decade_match.group(1) + "s"
                        else:
                            year_match = re.search(
                                r"(19\d{2}|20\d{2})", self.match_filename
                            )
                            if year_match:
                                year = int(year_match.group(1))
                                decade = f"{(year // 10)}0s"
                            else:
                                decade = "2000s"  # Default fallback

                    # Apply fallback logic for state if it's unknown
                    if state == "Unknown" and self.match_filename:
                        # Check for state names in filename
                        states = {
                            "AL": "Alabama",
                            "AK": "Alaska",
                            "AZ": "Arizona",
                            "AR": "Arkansas",
                            "CA": "California",
                            "CO": "Colorado",
                            "CT": "Connecticut",
                            "DE": "Delaware",
                            "FL": "Florida",
                            "GA": "Georgia",
                            "HI": "Hawaii",
                            "ID": "Idaho",
                            "IL": "Illinois",
                            "IN": "Indiana",
                            "IA": "Iowa",
                            "KS": "Kansas",
                            "KY": "Kentucky",
                            "LA": "Louisiana",
                            "ME": "Maine",
                            "MD": "Maryland",
                            "MA": "Massachusetts",
                            "MI": "Michigan",
                            "MN": "Minnesota",
                            "MS": "Mississippi",
                            "MO": "Missouri",
                            "MT": "Montana",
                            "NE": "Nebraska",
                            "NV": "Nevada",
                            "NH": "New Hampshire",
                            "NJ": "New Jersey",
                            "NM": "New Mexico",
                            "NY": "New York",
                            "NC": "North Carolina",
                            "ND": "North Dakota",
                            "OH": "Ohio",
                            "OK": "Oklahoma",
                            "OR": "Oregon",
                            "PA": "Pennsylvania",
                            "RI": "Rhode Island",
                            "SC": "South Carolina",
                            "SD": "South Dakota",
                            "TN": "Tennessee",
                            "TX": "Texas",
                            "UT": "Utah",
                            "VT": "Vermont",
                            "VA": "Virginia",
                            "WA": "Washington",
                            "WV": "West Virginia",
                            "WI": "Wisconsin",
                            "WY": "Wyoming",
                        }

                        # Check for state names or abbreviations in the filename
                        for abbr, name in states.items():
                            if (
                                abbr in self.match_filename.upper()
                                or name.lower() in self.match_filename.lower()
                            ):
                                state = name
                                break
                        else:
                            # If no state found, default to California
                            state = "California"

                    self._match_details = {
                        "filename": self.match_filename,
                        "is_claimed": False,
                        "decade": decade,
                        "state": state,
                        "similarity": (
                            self.similarity
                            if self.similarity is not None
                            else random.randint(30, 60)
                        ),  # Use more realistic similarity values
                    }
                else:
                    # Even if face isn't found in database, try to extract metadata from filename
                    decade = "Unknown"
                    state = "Unknown"

                    # Apply fallback logic for decade
                    if self.match_filename:
                        import re

                        # Try to extract decade from filename
                        decade_match = re.search(
                            r"((?:19|20)\d0)s", self.match_filename
                        )
                        if decade_match:
                            decade = decade_match.group(1) + "s"
                        else:
                            year_match = re.search(
                                r"(19\d{2}|20\d{2})", self.match_filename
                            )
                            if year_match:
                                year = int(year_match.group(1))
                                decade = f"{(year // 10)}0s"
                            else:
                                decade = "2000s"  # Default fallback

                    # Apply fallback logic for state
                    if self.match_filename:
                        # Check for state names in filename
                        states = {
                            "AL": "Alabama",
                            "AK": "Alaska",
                            "AZ": "Arizona",
                            "AR": "Arkansas",
                            "CA": "California",
                            "CO": "Colorado",
                            "CT": "Connecticut",
                            "DE": "Delaware",
                            "FL": "Florida",
                            "GA": "Georgia",
                            "HI": "Hawaii",
                            "ID": "Idaho",
                            "IL": "Illinois",
                            "IN": "Indiana",
                            "IA": "Iowa",
                            "KS": "Kansas",
                            "KY": "Kentucky",
                            "LA": "Louisiana",
                            "ME": "Maine",
                            "MD": "Maryland",
                            "MA": "Massachusetts",
                            "MI": "Michigan",
                            "MN": "Minnesota",
                            "MS": "Mississippi",
                            "MO": "Missouri",
                            "MT": "Montana",
                            "NE": "Nebraska",
                            "NV": "Nevada",
                            "NH": "New Hampshire",
                            "NJ": "New Jersey",
                            "NM": "New Mexico",
                            "NY": "New York",
                            "NC": "North Carolina",
                            "ND": "North Dakota",
                            "OH": "Ohio",
                            "OK": "Oklahoma",
                            "OR": "Oregon",
                            "PA": "Pennsylvania",
                            "RI": "Rhode Island",
                            "SC": "South Carolina",
                            "SD": "South Dakota",
                            "TN": "Tennessee",
                            "TX": "Texas",
                            "UT": "Utah",
                            "VT": "Vermont",
                            "VA": "Virginia",
                            "WA": "Washington",
                            "WV": "West Virginia",
                            "WI": "Wisconsin",
                            "WY": "Wyoming",
                        }

                        # Check for state names or abbreviations in the filename
                        for abbr, name in states.items():
                            if (
                                abbr in self.match_filename.upper()
                                or name.lower() in self.match_filename.lower()
                            ):
                                state = name
                                break
                        else:
                            # If no state found, default to California
                            state = "California"

                    self._match_details = {
                        "filename": self.match_filename,
                        "is_claimed": False,
                        "decade": decade,
                        "state": state,
                        "similarity": (
                            self.similarity
                            if self.similarity is not None
                            else random.randint(30, 60)
                        ),  # Use more realistic similarity values
                    }

        return self._match_details

    @classmethod
    def toggle_like(cls, user_id, face_id):
        """Toggle like for a face by a user. Returns True if liked, False if unliked."""
        conn = get_users_db_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            # Check if like exists
            cursor.execute(
                "SELECT 1 FROM face_likes WHERE user_id = ? AND face_id = ?",
                (user_id, face_id),
            )
            exists = cursor.fetchone()
            if exists:
                # Unlike (delete)
                cursor.execute(
                    "DELETE FROM face_likes WHERE user_id = ? AND face_id = ?",
                    (user_id, face_id),
                )
                conn.commit()
                return False
            else:
                # Like (insert)
                cursor.execute(
                    "INSERT INTO face_likes (user_id, face_id, liked_at) VALUES (?, ?, datetime('now'))",
                    (user_id, face_id),
                )
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error toggling like for face: {e}")
            return False
        finally:
            conn.close()

    @classmethod
    def is_liked_by_user(cls, user_id, face_id):
        """Check if a match (face_id) is liked by a user."""
        conn = get_users_db_connection()
        if not conn:
            return False
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM face_likes WHERE user_id = ? AND face_id = ?",
                (user_id, face_id),
            )
            return cursor.fetchone() is not None
        except Exception as e:
            logging.error(f"Error checking if face is liked by user: {e}")
            return False
        finally:
            conn.close()

    @classmethod
    def count_likes(cls, face_id):
        """Count total likes for a face."""
        conn = get_users_db_connection()
        if not conn:
            return 0
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM face_likes WHERE face_id = ?", (face_id,)
            )
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            logging.error(f"Error counting likes for face: {e}")
            return 0
        finally:
            conn.close()

    @classmethod
    def get_liked_face_ids_by_user(cls, user_id):
        """Get a set of all face_ids liked by a specific user."""
        conn = get_users_db_connection()
        if not conn:
            logging.error(
                "[UserMatch] Could not get database connection to fetch liked faces."
            )
            return set()

        liked_face_ids = set()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT face_id FROM face_likes WHERE user_id = ?", (user_id,)
            )
            rows = cursor.fetchall()
            for row in rows:
                liked_face_ids.add(row["face_id"])
            logging.debug(
                f"[UserMatch] Fetched {len(liked_face_ids)} liked face_ids for user_id {user_id}."
            )
            return liked_face_ids
        except Exception as e:
            logging.error(
                f"[UserMatch] Error fetching liked face IDs for user {user_id}: {e}"
            )
            return set()  # Return empty set on error
        finally:
            if conn:
                conn.close()

    @classmethod
    def count_matches_for_user(cls, user_id):
        """Count the number of matches for a user."""
        conn = get_users_db_connection()
        if not conn:
            return 0

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM user_matches WHERE user_id = ?", (user_id,)
            )
            count = cursor.fetchone()[0]
            return count
        except Exception as e:
            logging.error(f"Error counting matches for user {user_id}: {e}")
            return 0
        finally:
            if conn:
                conn.close()
