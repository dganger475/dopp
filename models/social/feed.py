"""Feed Models
============

Defines models for social media feeds and related operations.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from models.social.post import Post
from models.user import User
from utils.db.database import get_users_db_connection

class Feed:
    """Model for handling social media feeds."""

    @staticmethod
    def get_feed(user_id: Optional[int] = None, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get the social feed for a user.
        
        Args:
            user_id: Optional user ID to get personalized feed
            limit: Maximum number of posts to return
            offset: Number of posts to skip
            
        Returns:
            List of post dictionaries with user data
        """
        try:
            # Get posts from database
            posts = Post.get_feed(limit=limit, offset=offset)
            
            # Convert posts to dictionaries with user data
            return [
                post.to_dict(include_user=True, include_comments=True, user_id=user_id)
                for post in posts
            ]
            
        except Exception as e:
            logging.error(f"Error getting feed: {e}")
            return []

    @staticmethod
    def get_user_feed(user_id: int, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get posts from a specific user's feed.
        
        Args:
            user_id: User ID to get posts from
            limit: Maximum number of posts to return
            offset: Number of posts to skip
            
        Returns:
            List of post dictionaries with user data
        """
        try:
            # Get user's posts
            posts = Post.get_user_posts(user_id, limit=limit, offset=offset)
            
            # Convert posts to dictionaries with user data
            return [
                post.to_dict(include_user=True, include_comments=True, user_id=user_id)
                for post in posts
            ]
            
        except Exception as e:
            logging.error(f"Error getting user feed: {e}")
            return []

    @staticmethod
    def get_match_feed(user_id: int, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get posts about matches for a user.
        
        Args:
            user_id: User ID to get match posts for
            limit: Maximum number of posts to return
            offset: Number of posts to skip
            
        Returns:
            List of post dictionaries with user data
        """
        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT p.* FROM posts p
                WHERE p.is_match_post = 1
                AND (
                    p.user_id = ?
                    OR p.id IN (
                        SELECT post_id 
                        FROM post_mentions 
                        WHERE mentioned_user_id = ?
                    )
                )
                ORDER BY p.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, user_id, limit, offset)
            )

            posts = [Post(**dict(post_data)) for post_data in cursor.fetchall()]
            return [
                post.to_dict(include_user=True, include_comments=True, user_id=user_id)
                for post in posts
            ]

        except Exception as e:
            logging.error(f"Error getting match feed: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_trending_feed(limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get trending posts based on engagement.
        
        Args:
            limit: Maximum number of posts to return
            offset: Number of posts to skip
            
        Returns:
            List of post dictionaries with user data
        """
        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT p.*, 
                    COUNT(DISTINCT l.id) as like_count,
                    COUNT(DISTINCT c.id) as comment_count,
                    COUNT(DISTINCT r.id) as reaction_count
                FROM posts p
                LEFT JOIN likes l ON p.id = l.post_id
                LEFT JOIN comments c ON p.id = c.post_id
                LEFT JOIN reactions r ON p.id = r.post_id
                WHERE p.created_at >= datetime('now', '-7 days')
                GROUP BY p.id
                ORDER BY (like_count + comment_count + reaction_count) DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset)
            )

            posts = [Post(**dict(post_data)) for post_data in cursor.fetchall()]
            return [
                post.to_dict(include_user=True, include_comments=True)
                for post in posts
            ]

        except Exception as e:
            logging.error(f"Error getting trending feed: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_recommended_feed(user_id: int, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get recommended posts for a user based on their interests and activity.
        
        Args:
            user_id: User ID to get recommendations for
            limit: Maximum number of posts to return
            offset: Number of posts to skip
            
        Returns:
            List of post dictionaries with user data
        """
        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            # Get user's interests and activity
            cursor = conn.cursor()
            
            # Get posts from users the current user follows
            cursor.execute(
                """
                SELECT DISTINCT p.*
                FROM posts p
                JOIN follows f ON p.user_id = f.followed_id
                WHERE f.follower_id = ?
                AND p.created_at >= datetime('now', '-30 days')
                ORDER BY p.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, limit, offset)
            )

            posts = [Post(**dict(post_data)) for post_data in cursor.fetchall()]
            
            # If we don't have enough posts, get some trending posts
            if len(posts) < limit:
                remaining = limit - len(posts)
                cursor.execute(
                    """
                    SELECT p.*, 
                        COUNT(DISTINCT l.id) as like_count,
                        COUNT(DISTINCT c.id) as comment_count
                    FROM posts p
                    LEFT JOIN likes l ON p.id = l.post_id
                    LEFT JOIN comments c ON p.id = c.post_id
                    WHERE p.user_id != ?
                    AND p.created_at >= datetime('now', '-7 days')
                    GROUP BY p.id
                    ORDER BY (like_count + comment_count) DESC
                    LIMIT ?
                    """,
                    (user_id, remaining)
                )
                
                additional_posts = [Post(**dict(post_data)) for post_data in cursor.fetchall()]
                posts.extend(additional_posts)

            return [
                post.to_dict(include_user=True, include_comments=True, user_id=user_id)
                for post in posts
            ]

        except Exception as e:
            logging.error(f"Error getting recommended feed: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_mentions_feed(user_id: int, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get posts that mention a user.
        
        Args:
            user_id: User ID to get mentions for
            limit: Maximum number of posts to return
            offset: Number of posts to skip
            
        Returns:
            List of post dictionaries with user data
        """
        conn = get_users_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT p.* FROM posts p
                JOIN post_mentions pm ON p.id = pm.post_id
                WHERE pm.mentioned_user_id = ?
                ORDER BY p.created_at DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, limit, offset)
            )

            posts = [Post(**dict(post_data)) for post_data in cursor.fetchall()]
            return [
                post.to_dict(include_user=True, include_comments=True, user_id=user_id)
                for post in posts
            ]

        except Exception as e:
            logging.error(f"Error getting mentions feed: {e}")
            return []
        finally:
            conn.close() 