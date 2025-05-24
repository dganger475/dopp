import logging
import sqlite3
from flask import url_for
from utils.template_utils import get_image_path

"""
Social Models
=============

Defines data models for social features: posts, comments, likes, claimed profiles, and their relationships.
Handles logic for social interactions between users.
"""
from datetime import datetime

from flask import current_app

from models.user import User
from utils.db.database import get_users_db_connection


class Post:
    """Model for handling social media posts."""

    def __init__(self, id=None, user_id=None, content=None, **kwargs):
        self.id = id
        self.user_id = user_id
        self.content = content
        self.is_match_post = kwargs.get("is_match_post", 0)
        self.face_filename = kwargs.get("face_filename", None)
        self.created_at = kwargs.get(
            "created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self._user = None  # Cached user object
        self._comments = None  # Cached comments
        self._reactions = None  # Cached reactions
        self._likes = None  # Legacy: Cached likes count

    @classmethod
    def get_by_id(cls, post_id):
        """Get a post by its ID."""
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
            post_data = cursor.fetchone()

            if post_data:
                return cls(**dict(post_data))
            return None

        except Exception as e:
            logging.error(f"Error fetching post by id: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def create(cls, user_id, content, **kwargs):
        """
        Create a new post.

        Args:
            user_id: ID of the user creating the post
            content: Text content of the post
            **kwargs: Additional post attributes

        Returns:
            Post object if creation successful, None otherwise
        """
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()

            # Prepare the SQL statement with dynamic columns
            columns = ["user_id", "content"] + list(kwargs.keys())
            placeholders = ["?"] * (len(columns))
            values = [user_id, content] + list(kwargs.values())

            query = f"INSERT INTO posts ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            cursor.execute(query, values)
            conn.commit()

            # Get the new post's ID
            post_id = cursor.lastrowid

            # Return the new post
            return Post.get_by_id(post_id)

        except Exception as e:
            logging.error(f"Error creating post: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    @classmethod
    def get_feed(cls, limit=20, offset=0):
        """
        Get the latest posts for the main feed.

        Args:
            limit: Maximum number of posts to return
            offset: Offset for pagination

        Returns:
            List of Post objects
        """
        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM posts 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """,
                (limit, offset),
            )

            posts = []
            for post_data in cursor.fetchall():
                posts.append(cls(**dict(post_data)))

            return posts

        except Exception as e:
            logging.error(f"Error fetching feed: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    def get_user_posts(cls, user_id, limit=20, offset=0):
        """
        Get posts by a specific user.

        Args:
            user_id: ID of the user
            limit: Maximum number of posts to return
            offset: Offset for pagination

        Returns:
            List of Post objects
        """
        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM posts 
                WHERE user_id = ?
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """,
                (user_id, limit, offset),
            )

            posts = []
            for post_data in cursor.fetchall():
                posts.append(cls(**dict(post_data)))

            return posts

        except Exception as e:
            logging.error(f"Error fetching user posts: {e}")
            return []
        finally:
            conn.close()

    def update(self, content):
        """
        Update the post content.

        Args:
            content: New post content

        Returns:
            True if update successful, False otherwise
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
                UPDATE posts SET content = ? WHERE id = ?
            """,
                (content, self.id),
            )

            conn.commit()
            self.content = content
            return True

        except Exception as e:
            logging.error(f"Error updating post: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def delete(self):
        """
        Delete the post and associated comments and likes.

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

            # Delete comments and likes first
            cursor.execute("DELETE FROM comments WHERE post_id = ?", (self.id,))
            cursor.execute("DELETE FROM likes WHERE post_id = ?", (self.id,))

            # Delete the post
            cursor.execute("DELETE FROM posts WHERE id = ?", (self.id,))
            conn.commit()

            return True

        except Exception as e:
            logging.error(f"Error deleting post: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def get_user(self):
        """Get the user who created this post."""
        if self._user:
            return self._user

        if not self.user_id:
            return None

        self._user = User.get_by_id(self.user_id)
        return self._user

    def get_comments(self, refresh=False):
        """
        Get comments on this post.

        Args:
            refresh: Whether to refresh cached comments

        Returns:
            List of Comment objects
        """
        if self._comments is not None and not refresh:
            return self._comments

        if not self.id:
            return []

        self._comments = Comment.get_for_post(self.id)
        return self._comments

    def add_comment(self, user_id, content):
        """
        Add a comment to this post.

        Args:
            user_id: ID of the user making the comment
            content: Text content of the comment

        Returns:
            Comment object if successful, None otherwise
        """
        if not self.id:
            return None

        comment = Comment.create(self.id, user_id, content)

        # Refresh comments cache if we have one
        if self._comments is not None:
            self._comments.append(comment)

        return comment

    def get_reactions(self):
        """Get all reaction counts by type."""
        from models.reaction import Reaction

        if not self.id:
            return {rtype: 0 for rtype in Reaction.TYPES}
        return {
            rtype: Reaction.count_by_post(self.id, rtype) for rtype in Reaction.TYPES
        }

    def get_user_reaction(self, user_id):
        """Get a user's reaction to this post."""
        from models.reaction import Reaction

        if not self.id or not user_id:
            return None
        reaction = Reaction.get_by_user_and_post(user_id, self.id)
        return reaction.reaction_type if reaction else None

    def get_likes_count(self):
        """Legacy support: Get number of 'like' reactions."""
        from models.reaction import Reaction

        if not self.id:
            return 0

        conn = get_users_db_connection()
        if not conn:
            return 0

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) as count FROM likes WHERE post_id = ?
            """,
                (self.id,),
            )

            result = cursor.fetchone()
            self._likes = result["count"] if result else 0
            return self._likes

        except Exception as e:
            logging.error(f"Error counting likes: {e}")
            return 0
        finally:
            conn.close()

    def is_liked_by(self, user_id):
        """
        Check if this post is liked by a specific user.

        Args:
            user_id: ID of the user to check

        Returns:
            True if liked, False otherwise
        """
        if not self.id or not user_id:
            return False

        conn = get_users_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id FROM likes WHERE post_id = ? AND user_id = ?
            """,
                (self.id, user_id),
            )

            return cursor.fetchone() is not None

        except Exception as e:
            logging.error(f"Error checking like status: {e}")
            return False
        finally:
            conn.close()

    def toggle_like(self, user_id):
        """
        Toggle like status for a user.

        Args:
            user_id: ID of the user toggling like

        Returns:
            Tuple of (success, action) where action is 'liked' or 'unliked'
        """
        if not self.id or not user_id:
            return (False, None)

        conn = get_users_db_connection()
        if not conn:
            return (False, None)

        try:
            cursor = conn.cursor()

            # Check if already liked
            cursor.execute(
                """
                SELECT id FROM likes WHERE post_id = ? AND user_id = ?
            """,
                (self.id, user_id),
            )

            existing_like = cursor.fetchone()

            if existing_like:
                # Unlike
                cursor.execute(
                    """
                    DELETE FROM likes WHERE id = ?
                """,
                    (existing_like["id"],),
                )
                action = "unliked"
            else:
                # Like
                cursor.execute(
                    """
                    INSERT INTO likes (post_id, user_id) VALUES (?, ?)
                """,
                    (self.id, user_id),
                )
                action = "liked"

            conn.commit()

            # Refresh likes count
            self._likes = None
            self.get_likes_count(refresh=True)

            return (True, action)

        except Exception as e:
            logging.error(f"Error toggling like: {e}")
            if conn:
                conn.rollback()
            return (False, None)
        finally:
            if conn:
                conn.close()

    def get_comments_count(self):
        """Get the number of comments on this post."""
        conn = get_users_db_connection()
        if not conn:
            return 0

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM comments WHERE post_id = ?", (self.id,)
            )
            count = cursor.fetchone()[0]
            return count

        except Exception as e:
            logging.error(f"Error getting comments count: {e}")
            return 0
        finally:
            conn.close()

    def to_dict(self, include_user=True, include_comments=True, user_id=None):
        """Convert post to dictionary with user data.
        Adds match_card for match posts (side-by-side cards).
        """
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "content": self.content,
            "is_match_post": self.is_match_post,
            "face_filename": self.face_filename,
            "created_at": self.created_at,
            "reactions": self.get_reactions(),
            "likes_count": self.get_likes_count(),  # Legacy support
            "comments_count": self.get_comments_count(),
        }

        # Ensure user is loaded to get author details
        author = self.get_user() # Call get_user() to load/retrieve the author

        if author: # Check if author was successfully loaded
            user_dict = author.to_dict() # Use the loaded author object
            # Use get_image_path for profile images with proper fallback
            profile_image_filename = user_dict.get("profile_image") # Filename from User.to_dict()
            
            # Generate profile image URL using get_image_path with fallback to default
            # Pass '' for subfolder so get_image_path checks its default locations like 'profile_pics/' directly.
            profile_image_url = get_image_path(profile_image_filename, '') if profile_image_filename else get_image_path('default-profile.png', '')
            
            # Store both the original filename and the full URL
            data["profile_image"] = profile_image_filename # Raw filename
            data["profile_image_url"] = profile_image_url # This should be the URL
            data["username"] = user_dict.get("username", "Unknown User")
            data["profile_url"] = f"/profile/{user_dict.get('username', '')}"
            
            # Add user object with profile image URL
            data["user"] = {
                "username": data["username"],
                "profile_image": profile_image_filename, # Raw filename
                "profile_image_url": profile_image_url # URL for the template
            }

        if user_id:
            data["user_has_liked"] = self.is_liked_by(user_id)

        # --- MATCH CARD LOGIC ---
        if self.is_match_post and self.face_filename:
            # Prepare user card (posting user)
            user = self._user or User.get_by_id(self.user_id)
            user_card = {
                "is_registered": True,
                "username": user.username,
                "city": f"{user.current_location_city}, {user.current_location_state}" if user.current_location_city and user.current_location_state else user.current_location_city or user.hometown or "",
                "cover_photo_url": (
                    user.get_cover_photo_url()
                    if hasattr(user, "get_cover_photo_url")
                    else ""
                ),
                "profile_url": f"/profile/{user.username}",
            }
            # Prepare match card (could be registered or not)
            from models.face import Face

            match_face = Face.get_by_filename(self.face_filename)
            match_user = None
            if match_face and hasattr(match_face, "user_id") and match_face.user_id:
                from models.user import User as MatchUser

                match_user = MatchUser.get_by_id(match_face.user_id)
            if match_user:
                match_card = {
                    "is_registered": True,
                    "username": match_user.username,
                    "city": f"{match_user.current_location_city}, {match_user.current_location_state}" if match_user.current_location_city and match_user.current_location_state else match_user.current_location_city or match_user.hometown or "",
                    "cover_photo_url": (
                        match_user.get_cover_photo_url()
                        if hasattr(match_user, "get_cover_photo_url")
                        else ""
                    ),
                    "profile_url": f"/profile/{match_user.username}",
                }
            else:
                match_card = {
                    "is_registered": False,
                    "username": "",
                    "city": "",
                    "cover_photo_url": "",
                    "comparison_url": (
                        f"/comparison/face/{self.face_filename}"
                        if self.face_filename
                        else ""
                    ),
                }
            data["match_card"] = {"user": user_card, "match": match_card}

        return data


class ClaimedProfile:
    """Model for handling claimed face profiles."""

    def __init__(self, id=None, user_id=None, face_filename=None, **kwargs):
        self.id = id
        self.user_id = user_id
        self.face_filename = face_filename
        self.relationship = kwargs.get("relationship", "No relation")
        self.caption = kwargs.get("caption", "")
        self.claimed_at = kwargs.get(
            "claimed_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self._user = None  # Cached user object
        self._face_data = None  # Cached face data

    @classmethod
    def get_by_id(cls, profile_id):
        """Get a claimed profile by its ID."""
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM claimed_profiles WHERE id = ?", (profile_id,))
            profile_data = cursor.fetchone()

            if profile_data:
                return cls(**dict(profile_data))
            return None

        except Exception as e:
            logging.error(f"Error fetching claimed profile by id: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def get_by_filename(cls, filename):
        """Get a claimed profile by its face filename."""
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM claimed_profiles WHERE face_filename = ?", (filename,)
            )
            profile_data = cursor.fetchone()

            if profile_data:
                return cls(**dict(profile_data))
            return None

        except Exception as e:
            logging.error(f"Error fetching claimed profile by filename: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def get_by_user_id(cls, user_id):
        """Get all claimed profiles belonging to a user.

        Args:
            user_id: The ID of the user

        Returns:
            List of ClaimedProfile objects
        """
        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM claimed_profiles 
                WHERE user_id = ? 
                ORDER BY claimed_at DESC
            """,
                (user_id,),
            )

            profiles = []
            for profile_data in cursor.fetchall():
                profiles.append(cls(**dict(profile_data)))

            return profiles

        except Exception as e:
            logging.error(f"Error fetching claimed profiles by user id: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    def is_claimed(cls, filename):
        """Check if a face profile is claimed."""
        return cls.get_by_filename(filename) is not None

    @classmethod
    def create(
        cls,
        user_id,
        face_filename,
        relationship="No relation",
        caption="",
        share_to_feed=True,
    ):
        """
        Claim a face profile.

        Args:
            user_id: ID of the user claiming the profile
            face_filename: Filename of the face
            relationship: Relationship description
            caption: User-provided caption
            share_to_feed: Whether to create a post about this claim

        Returns:
            ClaimedProfile object if successful, None otherwise
        """
        conn = get_users_db_connection()
        if not conn:
            return None

        # Check if already claimed
        if cls.is_claimed(face_filename):
            return None

        try:
            cursor = conn.cursor()

            # Create the claim
            cursor.execute(
                """
                INSERT INTO claimed_profiles (user_id, face_filename, relationship, caption)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, face_filename, relationship, caption),
            )

            # Create a post if requested
            if share_to_feed:
                post_content = "I claimed a historical twin!"
                if caption:
                    post_content += f" {caption}"

                cursor.execute(
                    """
                    INSERT INTO posts (user_id, content, is_match_post, face_filename)
                    VALUES (?, ?, 1, ?)
                    """,
                    (user_id, post_content, face_filename),
                )

            conn.commit()

            # Return the new claimed profile
            return cls.get_by_filename(face_filename)

        except Exception as e:
            logging.error(f"Error creating claimed profile: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    def get_user(self):
        """Get the user who claimed this profile."""
        if self._user:
            return self._user

        if not self.user_id:
            return None

        self._user = User.get_by_id(self.user_id)
        return self._user

    def get_face_data(self):
        """Get face data for this claimed profile."""
        if self._face_data:
            return self._face_data

        if not self.face_filename:
            return None

        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM faces WHERE filename = ?", (self.face_filename,)
            )
            face_data = cursor.fetchone()

            if face_data:
                self._face_data = dict(face_data)
                return self._face_data
            return None

        except Exception as e:
            logging.error(f"Error fetching face data: {e}")
            return None
        finally:
            conn.close()

    def get_or_create_user_match(self):
        """
        Get or create a UserMatch object for this claimed profile.
        This is used for privacy protection - allowing us to use match IDs
        instead of exposing filenames in templates and URLs.

        Returns:
            UserMatch object or None if there was an error
        """
        from models.user_match import UserMatch

        try:
            # First check if a match already exists for this user and filename
            existing_match = UserMatch.get_by_user_and_filename(
                self.user_id, self.face_filename
            )
            if existing_match:
                return existing_match

            # If no match exists, create a new one
            # Set privacy level to public since this is a claimed profile that the user has chosen to share
            new_match = UserMatch.add_match(
                user_id=self.user_id,
                match_filename=self.face_filename,
                is_visible=1,  # Visible by default
                privacy_level="public",  # Public by default for claimed profiles
            )

            return new_match

        except Exception as e:
            logging.error(f"Error creating user match: {e}")
            return None

    @classmethod
    def get_trending(cls, limit=5):
        """Get trending claimed profiles based on interaction counts.

        Args:
            limit: Maximum number of profiles to return

        Returns:
            List of ClaimedProfile objects
        """
        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            # Get profiles with most interactions (comments + likes + reactions)
            cursor.execute(
                """
                SELECT cp.*, 
                    COUNT(DISTINCT c.id) + COUNT(DISTINCT l.id) + COUNT(DISTINCT r.id) as interaction_count
                FROM claimed_profiles cp
                LEFT JOIN posts p ON p.face_filename = cp.face_filename
                LEFT JOIN comments c ON c.post_id = p.id
                LEFT JOIN likes l ON l.post_id = p.id
                LEFT JOIN reactions r ON r.post_id = p.id
                GROUP BY cp.id
                ORDER BY interaction_count DESC
                LIMIT ?
            """,
                (limit,),
            )

            profiles = []
            for profile_data in cursor.fetchall():
                profiles.append(cls(**dict(profile_data)))

            return profiles

        except Exception as e:
            logging.error(f"Error getting trending profiles: {e}")
            return []
        finally:
            conn.close()

    def to_dict(self, include_user=True, include_face_data=True):
        """
        Convert claimed profile to dictionary.

        Args:
            include_user: Whether to include user data
            include_face_data: Whether to include face data

        Returns:
            Dictionary with claimed profile data
        """
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "face_filename": self.face_filename,
            "relationship": self.relationship,
            "caption": self.caption,
            "claimed_at": self.claimed_at,
        }

        if include_user:
            user = self.get_user()
            if user:
                data["user"] = user.to_dict()

        if include_face_data:
            face_data = self.get_face_data()
            if face_data:
                data["face_data"] = face_data

        return data


class Comment:
    """Model for handling post comments."""

    def __init__(self, id=None, post_id=None, user_id=None, content=None, **kwargs):
        self.id = id
        self.post_id = post_id
        self.user_id = user_id
        self.content = content
        self.parent_id = kwargs.get("parent_id", None)  # For threaded comments
        self.created_at = kwargs.get(
            "created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self._user = None  # Cached user object
        self._replies = None  # Cached replies

    @classmethod
    def get_by_id(cls, comment_id):
        """Get a comment by its ID."""
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM comments WHERE id = ?", (comment_id,))
            comment_data = cursor.fetchone()

            if comment_data:
                return cls(**dict(comment_data))
            return None

        except Exception as e:
            logging.error(f"Error fetching comment by id: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def get_by_post(cls, post_id, include_replies=True):
        """Get all comments for a post.

        Args:
            post_id: ID of the post
            include_replies: Whether to include threaded replies

        Returns:
            List of Comment objects
        """
        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            if include_replies:
                cursor.execute(
                    """
                    SELECT * FROM comments 
                    WHERE post_id = ? 
                    ORDER BY 
                        CASE WHEN parent_id IS NULL THEN id ELSE parent_id END,
                        parent_id IS NOT NULL,
                        id
                """,
                    (post_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM comments 
                    WHERE post_id = ? AND parent_id IS NULL
                    ORDER BY id
                """,
                    (post_id,),
                )

            comments = []
            for comment_data in cursor.fetchall():
                comments.append(cls(**dict(comment_data)))

            return comments

        except Exception as e:
            logging.error(f"Error fetching comments by post id: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    def create(cls, post_id, user_id, content, parent_id=None):
        """Create a new comment.

        Args:
            post_id: ID of the post being commented on
            user_id: ID of the user making the comment
            content: Comment text
            parent_id: ID of parent comment if this is a reply

        Returns:
            Comment object if successful, None otherwise
        """
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()

            # Verify the parent comment exists and belongs to the same post
            if parent_id:
                cursor.execute(
                    """
                    SELECT post_id FROM comments 
                    WHERE id = ? AND post_id = ?
                """,
                    (parent_id, post_id),
                )
                if not cursor.fetchone():
                    return None

            cursor.execute(
                """
                INSERT INTO comments (post_id, user_id, content, parent_id)
                VALUES (?, ?, ?, ?)
                """,
                (post_id, user_id, content, parent_id),
            )

            conn.commit()

            # Return the new comment
            return cls.get_by_id(cursor.lastrowid)

        except Exception as e:
            logging.error(f"Error creating comment: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    def get_user(self):
        """Get the user who made this comment."""
        if self._user is not None:
            return self._user

        if not self.user_id:
            return None

        self._user = User.get_by_id(self.user_id)
        return self._user

    def get_replies(self):
        """Get replies to this comment."""
        if self._replies is not None:
            return self._replies

        if not self.id:
            return []

        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM comments 
                WHERE parent_id = ? 
                ORDER BY id
            """,
                (self.id,),
            )

            replies = []
            for reply_data in cursor.fetchall():
                replies.append(Comment(**dict(reply_data)))

            self._replies = replies
            return replies

        except Exception as e:
            logging.error(f"Error fetching comment replies: {e}")
            return []
        finally:
            conn.close()

    def to_dict(self, include_user=True, include_replies=True):
        """Convert comment to dictionary.

        Args:
            include_user: Whether to include user data
            include_replies: Whether to include replies

        Returns:
            Dictionary with comment data
        """
        data = {
            "id": self.id,
            "post_id": self.post_id,
            "user_id": self.user_id,
            "content": self.content,
            "parent_id": self.parent_id,
            "created_at": self.created_at,
        }

        if include_user:
            user = self.get_user()
            if user:
                user_dict = user.to_dict()
                # Add profile_image_url for consistent image handling
                profile_image = user_dict.get("profile_image")
                
                # Generate profile image URL using get_image_path with fallback to default
                profile_image_url = get_image_path(profile_image, '') if profile_image else get_image_path('default_profile.png', '')
                
                # Store both the original and the full URL
                data["profile_image"] = profile_image
                data["profile_image_url"] = profile_image_url
                data["username"] = user_dict.get("username", "Unknown User")
                data["profile_url"] = f"/profile/{user_dict.get('username', '')}"
                
                # Add user object with profile image URL
                data["user"] = {
                    "username": data["username"],
                    "profile_image": profile_image,
                    "profile_image_url": profile_image_url,
                    "profile_url": data["profile_url"]
                }

        if include_replies:
            replies = self.get_replies()
            if replies:
                data["replies"] = [
                    reply.to_dict(include_replies=False) for reply in replies
                ]

        return data


class Like:
    """Model for handling post likes (legacy)."""

    def __init__(self, id=None, post_id=None, user_id=None, **kwargs):
        self.id = id
        self.post_id = post_id
        self.user_id = user_id
        self.created_at = kwargs.get(
            "created_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self._user = None  # Cached user object

    @classmethod
    def get_by_id(cls, like_id):
        """Get a like by its ID."""
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM likes WHERE id = ?", (like_id,))
            like_data = cursor.fetchone()

            if like_data:
                return cls(**dict(like_data))
            return None

        except Exception as e:
            logging.error(f"Error fetching like by id: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def get_by_post_and_user(cls, post_id, user_id):
        """Get a like by post and user IDs."""
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM likes WHERE post_id = ? AND user_id = ?",
                (post_id, user_id),
            )
            like_data = cursor.fetchone()

            if like_data:
                return cls(**dict(like_data))
            return None

        except Exception as e:
            logging.error(f"Error fetching like by post and user: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def get_by_post(cls, post_id):
        """Get all likes for a post.

        Args:
            post_id: ID of the post

        Returns:
            List of Like objects
        """
        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM likes WHERE post_id = ?", (post_id,))

            likes = []
            for like_data in cursor.fetchall():
                likes.append(cls(**dict(like_data)))

            return likes

        except Exception as e:
            logging.error(f"Error fetching likes by post id: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    def create(cls, post_id, user_id):
        """Create a new like.

        Args:
            post_id: ID of the post being liked
            user_id: ID of the user liking the post

        Returns:
            Like object if successful, None otherwise
        """
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()

            # Check if already liked
            existing_like = cls.get_by_post_and_user(post_id, user_id)
            if existing_like:
                return existing_like

            cursor.execute(
                "INSERT INTO likes (post_id, user_id) VALUES (?, ?)", (post_id, user_id)
            )

            conn.commit()

            # Return the new like
            return cls.get_by_id(cursor.lastrowid)

        except Exception as e:
            logging.error(f"Error creating like: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    @classmethod
    def delete(cls, post_id, user_id):
        """Delete a like.

        Args:
            post_id: ID of the post
            user_id: ID of the user

        Returns:
            True if successful, False otherwise
        """
        conn = get_users_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM likes WHERE post_id = ? AND user_id = ?",
                (post_id, user_id),
            )

            conn.commit()
            return True

        except Exception as e:
            logging.error(f"Error deleting like: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def get_user(self):
        """Get the user who made this like."""
        if self._user is not None:
            return self._user

        if not self.user_id:
            return None

        self._user = User.get_by_id(self.user_id)
        return self._user

    def to_dict(self, include_user=True):
        """Convert like to dictionary.

        Args:
            include_user: Whether to include user data

        Returns:
            Dictionary with like data
        """
        data = {
            "id": self.id,
            "post_id": self.post_id,
            "user_id": self.user_id,
            "created_at": self.created_at,
        }

        if include_user:
            user = self.get_user()
            if user:
                data["user"] = user.to_dict()

        return data

    def get_comments_count(self):
        """Get the number of comments on this post."""
        conn = get_users_db_connection()
        if not conn:
            return 0

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM comments WHERE post_id = ?", (self.id,)
            )
            count = cursor.fetchone()[0]
            return count

        except Exception as e:
            logging.error(f"Error getting comments count: {e}")
            return 0
        finally:
            conn.close()

    def get_reactions_count(self, reaction_type=None):
        """Get number of reactions for this post."""
        from models.reaction import Reaction

        return Reaction.count_by_post(self.id, reaction_type)

    def get_likes_count(self):
        """Get number of likes for this post (legacy support)."""
        return self.get_reactions_count("like")

    def get_reactions(self):
        """Get reaction counts by type."""
        from models.reaction import Reaction

        return {
            reaction_type: self.get_reactions_count(reaction_type)
            for reaction_type in Reaction.TYPES
        }

    # ... (rest of the code remains the same)
    def __init__(self, id=None, user_id=None, face_filename=None, **kwargs):
        self.id = id
        self.user_id = user_id
        self.face_filename = face_filename
        self.relationship = kwargs.get("relationship", "No relation")
        self.caption = kwargs.get("caption", "")
        self.claimed_at = kwargs.get(
            "claimed_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        self._user = None  # Cached user object
        self._face_data = None  # Cached face data

    @classmethod
    def get_by_id(cls, profile_id):
        """Get a claimed profile by its ID."""
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM claimed_profiles WHERE id = ?", (profile_id,))
            profile_data = cursor.fetchone()

            if profile_data:
                return cls(**dict(profile_data))
            return None

        except Exception as e:
            logging.error(f"Error fetching claimed profile by id: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def get_by_filename(cls, filename):
        """Get a claimed profile by its face filename."""
        conn = get_users_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM claimed_profiles WHERE face_filename = ?", (filename,)
            )
            profile_data = cursor.fetchone()

            if profile_data:
                return cls(**dict(profile_data))
            return None

        except Exception as e:
            logging.error(f"Error fetching claimed profile by filename: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def get_by_user_id(cls, user_id):
        """Get all claimed profiles belonging to a user.

        Args:
            user_id: The ID of the user

        Returns:
            List of ClaimedProfile objects
        """
        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM claimed_profiles 
                WHERE user_id = ? 
                ORDER BY claimed_at DESC
            """,
                (user_id,),
            )

            profiles = []
            for profile_data in cursor.fetchall():
                profiles.append(cls(**dict(profile_data)))

            return profiles

        except Exception as e:
            logging.error(f"Error fetching claimed profiles by user id: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    def is_claimed(cls, filename):
        """Check if a face profile is claimed."""
        return cls.get_by_filename(filename) is not None

    @classmethod
    def create(
        cls,
        user_id,
        face_filename,
        relationship="No relation",
        caption="",
        share_to_feed=True,
    ):
        """
        Claim a face profile.

        Args:
            user_id: ID of the user claiming the profile
            face_filename: Filename of the face
            relationship: Relationship description
            caption: User-provided caption
            share_to_feed: Whether to create a post about this claim

        Returns:
            ClaimedProfile object if successful, None otherwise
        """
        conn = get_users_db_connection()
        if not conn:
            return None

        # Check if already claimed
        if cls.is_claimed(face_filename):
            return None

        try:
            cursor = conn.cursor()

            # Create the claim
            cursor.execute(
                """
                INSERT INTO claimed_profiles (user_id, face_filename, relationship, caption)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, face_filename, relationship, caption),
            )

            # Create a post if requested
            if share_to_feed:
                post_content = "I claimed a historical twin!"
                if caption:
                    post_content += f" {caption}"

                cursor.execute(
                    """
                    INSERT INTO posts (user_id, content, is_match_post, face_filename)
                    VALUES (?, ?, 1, ?)
                    """,
                    (user_id, post_content, face_filename),
                )

            conn.commit()

            # Get the new claim's ID
            claim_id = cursor.lastrowid

            # Return the new claim
            return ClaimedProfile.get_by_id(claim_id)

        except Exception as e:
            logging.error(f"Error claiming profile: {e}")
            if conn:
                conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    @classmethod
    def get_recent_claims(cls, limit=10):
        """
        Get recently claimed profiles.

        Args:
            limit: Maximum number of claims to return

        Returns:
            List of ClaimedProfile objects
        """
        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM claimed_profiles 
                ORDER BY claimed_at DESC 
                LIMIT ?
            """,
                (limit,),
            )

            claims = []
            for claim_data in cursor.fetchall():
                claims.append(cls(**dict(claim_data)))

            return claims

        except Exception as e:
            logging.error(f"Error fetching recent claims: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    def get_recent(cls, limit=10):
        """
        Alias for get_recent_claims to maintain compatibility with existing code.

        Args:
            limit: Maximum number of claims to return

        Returns:
            List of ClaimedProfile objects
        """
        return cls.get_recent_claims(limit=limit)

    @classmethod
    def get_trending(cls, limit=5):
        """
        Get trending claimed profiles (currently just returns recent claims).
        In a real implementation, this would use metrics like views, likes, etc.

        Args:
            limit: Maximum number of profiles to return

        Returns:
            List of ClaimedProfile objects
        """
        # For now, we'll just return recent claims as a placeholder
        # In a real implementation, we would use metrics like views, likes, etc.
        return cls.get_recent_claims(limit=limit)

    def unclaim(self):
        """
        Unclaim a profile (delete the claim).

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
            cursor.execute("DELETE FROM claimed_profiles WHERE id = ?", (self.id,))
            conn.commit()

            return True

        except Exception as e:
            logging.error(f"Error unclaiming profile: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def get_user(self):
        """Get the user who claimed this profile."""
        if self._user:
            return self._user

        if not self.user_id:
            return None

        self._user = User.get_by_id(self.user_id)
        return self._user

    def get_face_data(self):
        """Get the face data for this claimed profile."""
        if self._face_data:
            return self._face_data

        if not self.face_filename:
            return None

        # Connect to the faces database
        conn = sqlite3.connect(current_app.config["DB_PATH"])
        conn.row_factory = sqlite3.Row

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM faces WHERE filename = ?", (self.face_filename,)
            )
            face_data = cursor.fetchone()

            if face_data:
                self._face_data = dict(face_data)
                return self._face_data
            return None

        except Exception as e:
            logging.error(f"Error fetching face data: {e}")
            return None
        finally:
            conn.close()

    def get_or_create_user_match(self):
        """
        Get or create a UserMatch object for this claimed profile.
        This is used for privacy protection - allowing us to use match IDs
        instead of exposing filenames in templates and URLs.

        Returns:
            UserMatch object or None if there was an error
        """
        from models.user_match import UserMatch

        try:
            # First check if a match already exists for this user and filename
            existing_match = UserMatch.get_by_user_and_filename(
                self.user_id, self.face_filename
            )
            if existing_match:
                return existing_match

            # If no match exists, create a new one
            # Set privacy level to public since this is a claimed profile that the user has chosen to share
            new_match = UserMatch.add_match(
                user_id=self.user_id,
                match_filename=self.face_filename,
                is_visible=1,  # Visible by default
                privacy_level="public",  # Public by default for claimed profiles
            )

            return new_match

        except Exception as e:
            logging.error(f"Error creating user match: {e}")
            return None
            existing_match = UserMatch.get_by_user_and_filename(
                self.user_id, self.face_filename
            )
            if existing_match:
                return existing_match

            # If no match exists, create a new one
            # Set privacy level to public since this is a claimed profile that the user has chosen to share
            new_match = UserMatch.add_match(
                user_id=self.user_id,
                match_filename=self.face_filename,
                is_visible=1,  # Visible by default
                privacy_level="public",  # Public by default for claimed profiles
            )

            return new_match

        except Exception as e:
            logging.error(f"Error creating user match: {e}")
            return None


def to_dict(self, include_user=True, include_face_data=True, include_comments=False):
    """
    Convert claimed profile to dictionary.

    Args:
        include_user: Whether to include user data
        include_face_data: Whether to include face data
        include_comments: Whether to include comments

    Returns:
        Dictionary with claimed profile data
    """
    data = {
        "id": self.id,
        "user_id": self.user_id,
        "face_filename": self.face_filename,
        "relationship": self.relationship,
        "caption": self.caption,
        "claimed_at": self.claimed_at,
    }

    if include_user:
        user = self.get_user()
        if user:
            data["user"] = user.to_dict()

    if include_comments:
        comments = self.get_comments()
        if comments:
            data["comments"] = [comment.to_dict() for comment in comments]

    if include_face_data:
        face_data = self.get_face_data()
        if face_data:
            data["face_data"] = face_data

    return data
