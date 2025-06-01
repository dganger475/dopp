"""Social Services
==============

This module provides service layer functionality for social features,
handling business logic and coordinating between models.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.social.post import Post
from models.social.feed import Feed
from models.social.interaction import Comment, Like, Reaction, Share
from models.social.notification import Notification
from models.user import User
from utils.cache import cache
from utils.db.database import get_users_db_connection

logger = logging.getLogger(__name__)

class SocialService:
    """Service for handling social features."""
    
    @staticmethod
    @cache.memoize(timeout=300)
    def get_user_feed(user_id: int, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get the social feed for a user with caching."""
        try:
            return Feed.get_user_feed(user_id, limit, offset)
        except Exception as e:
            logger.error(f"Error getting user feed: {e}")
            return []

    @staticmethod
    def create_post(user_id: int, content: str, is_match_post: bool = False) -> Optional[Post]:
        """Create a new post with notification handling."""
        try:
            post = Post.create(
                user_id=user_id,
                content=content,
                is_match_post=is_match_post
            )
            
            # Clear feed cache for the user
            cache.delete_memoized(SocialService.get_user_feed, user_id)
            
            return post
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            return None

    @staticmethod
    def add_comment(post_id: int, user_id: int, content: str) -> Optional[Comment]:
        """Add a comment to a post with notification."""
        try:
            post = Post.get_by_id(post_id)
            if not post:
                return None
                
            comment = Comment.create(
                post_id=post_id,
                user_id=user_id,
                content=content
            )
            
            # Create notification for post owner
            if post.user_id != user_id:
                Notification.create(
                    user_id=post.user_id,
                    type="comment",
                    data={
                        "post_id": post_id,
                        "comment_id": comment.id,
                        "user_id": user_id
                    }
                )
            
            return comment
        except Exception as e:
            logger.error(f"Error adding comment: {e}")
            return None

    @staticmethod
    def add_reaction(post_id: int, user_id: int, reaction_type: str) -> Optional[Reaction]:
        """Add a reaction to a post with notification."""
        try:
            post = Post.get_by_id(post_id)
            if not post:
                return None
                
            # Check if user already reacted
            existing_reaction = Reaction.get_by_user_and_post(user_id, post_id)
            if existing_reaction:
                if existing_reaction.reaction_type == reaction_type:
                    return existing_reaction
                existing_reaction.update(reaction_type=reaction_type)
                return existing_reaction
            
            reaction = Reaction.create(
                post_id=post_id,
                user_id=user_id,
                reaction_type=reaction_type
            )
            
            # Create notification for post owner
            if post.user_id != user_id:
                Notification.create(
                    user_id=post.user_id,
                    type="reaction",
                    data={
                        "post_id": post_id,
                        "reaction_id": reaction.id,
                        "user_id": user_id,
                        "reaction_type": reaction_type
                    }
                )
            
            return reaction
        except Exception as e:
            logger.error(f"Error adding reaction: {e}")
            return None

    @staticmethod
    def share_post(post_id: int, user_id: int) -> Optional[Share]:
        """Share a post with notification."""
        try:
            post = Post.get_by_id(post_id)
            if not post:
                return None
                
            share = Share.create(
                post_id=post_id,
                user_id=user_id
            )
            
            # Create notification for post owner
            if post.user_id != user_id:
                Notification.create(
                    user_id=post.user_id,
                    type="share",
                    data={
                        "post_id": post_id,
                        "share_id": share.id,
                        "user_id": user_id
                    }
                )
            
            return share
        except Exception as e:
            logger.error(f"Error sharing post: {e}")
            return None

    @staticmethod
    def get_trending_posts(limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending posts with caching."""
        cache_key = f"trending_posts_{limit}"
        cached_posts = cache.get(cache_key)
        if cached_posts:
            return cached_posts
            
        try:
            posts = Feed.get_trending_feed(limit=limit)
            cache.set(cache_key, posts, timeout=300)  # Cache for 5 minutes
            return posts
        except Exception as e:
            logger.error(f"Error getting trending posts: {e}")
            return []

    @staticmethod
    def get_user_notifications(user_id: int, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get user notifications with pagination."""
        try:
            notifications = Notification.get_for_user(user_id, limit, offset)
            return [n.to_dict() for n in notifications]
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []

    @staticmethod
    def mark_notification_as_read(notification_id: int, user_id: int) -> bool:
        """Mark a notification as read."""
        try:
            notification = Notification.get_by_id(notification_id)
            if not notification or notification.user_id != user_id:
                return False
                
            notification.mark_as_read()
            return True
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False

    @staticmethod
    def delete_post(post_id: int, user_id: int) -> bool:
        """Delete a post and its associated data."""
        try:
            post = Post.get_by_id(post_id)
            if not post or post.user_id != user_id:
                return False
                
            # Delete associated data
            conn = get_users_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))
                cursor.execute("DELETE FROM likes WHERE post_id = ?", (post_id,))
                cursor.execute("DELETE FROM reactions WHERE post_id = ?", (post_id,))
                cursor.execute("DELETE FROM shares WHERE post_id = ?", (post_id,))
                conn.commit()
            finally:
                conn.close()
            
            # Delete the post
            post.delete()
            
            # Clear feed cache
            cache.delete_memoized(SocialService.get_user_feed, user_id)
            
            return True
        except Exception as e:
            logger.error(f"Error deleting post: {e}")
            return False 