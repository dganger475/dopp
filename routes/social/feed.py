"""
Feed Routes Module
================

This module contains routes related to the social feed, including:
- Post creation and management
- Feed timeline
- Feed filtering and sorting
"""
import logging
import os
# import time # Not needed for timing if done globally in app.py
# from datetime import datetime # Not directly used in current routes

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

# Review these model imports - keep only what's directly used in this file's routes
# from models.social import ClaimedProfile, Comment, Like # Not directly used here
from models.social import Post, Like, Comment
from models.user import User
from routes.auth import login_required
from models.user_match import UserMatch # Needed for share_match
from models.notification import Notification # Needed for share_match

feed = Blueprint('feed', __name__)

# --- Section: Feed and Social Home ---

@feed.route("/share_match", methods=["POST"])
@login_required
def share_match():
    """Share a match to the feed as a post."""
    user_id = session.get("user_id")
    match_filename = request.form.get("match_filename")
    if not match_filename:
        # Assuming face_matching blueprint and view_profile_matches route exist
        return redirect(
            url_for(
                "face_matching.view_profile_matches",
                share_error="Missing match filename",
            )
        )
    # TODO: Implement check to ensure the match_filename actually belongs to the current_user_id
    #       or is otherwise permissible for them to share. This is important for security and data integrity.
    # Optional: Check if the match belongs to the user
    # Create a post referencing this match
    # Privacy: Do NOT include the filename in the post content
    content = "I found my historical doppelganger!"
    post = Post.create(
        user_id=user_id, content=content, is_match_post=1, face_filename=match_filename
    )
    # Notify original match owner if not current user
    match = UserMatch.get_by_user_and_filename(user_id, match_filename)
    if match and match.user_id != user_id:
        Notification.create(
            user_id=match.user_id,
            type=Notification.TYPE_MATCH_CLAIMED if hasattr(Notification, 'TYPE_MATCH_CLAIMED') else 'match_claimed',
            content="Your match card was shared to the feed!",
            entity_id=match.id,
            entity_type="match",
            sender_id=user_id
        )
    if post:
        # Assuming face_matching blueprint and view_profile_matches route exist
        return redirect(url_for("face_matching.view_profile_matches", share_success=1))
    else:
         # Assuming face_matching blueprint and view_profile_matches route exist
        return redirect(
            url_for(
                "face_matching.view_profile_matches",
                share_error="Failed to share match to feed",
            )
        )

@feed.route("/", strict_slashes=False)
@login_required
def feed_page():
    """Display the social feed."""
    user_id = session.get("user_id")

    # Create a test post if no posts exist
    posts = Post.get_feed()
    if not posts:
        test_post = Post.create(
            user_id=user_id,
            content="Welcome to your social feed! This is a test post.",
            is_match_post=0
        )
        if test_post:
            posts = [test_post]

    # Ensure posts are dictionaries with user/profile info
    posts = [post.to_dict(user_id=user_id) for post in posts]

    return jsonify({
        "posts": posts,
        "success": True
    })

@feed.route("/create_post", methods=["POST"])
@login_required
def create_post():
    """Create a new post."""
    user_id = session.get("user_id")
    content = request.form.get("content")
    face_filename = request.form.get("face_filename")

    if not content and not face_filename:
        return jsonify({
            "success": False,
            "error": "Post content or image is required"
        }), 400

    try:
        post = Post.create(
            user_id=user_id,
            content=content,
            face_filename=face_filename
        )

        if post:
            return jsonify({
                "success": True,
                "message": "Post created successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to create post"
            }), 500

    except Exception as e:
        current_app.logger.error(f"Error creating post for user {user_id}: {e}")
        return jsonify({
            "success": False,
            "error": "An error occurred while creating the post"
        }), 500

@feed.route("/like/<int:post_id>", methods=["POST"])
@login_required
def like_post(post_id):
    """Like or unlike a post."""
    user_id = session.get("user_id")
    
    try:
        post = Post.get_by_id(post_id)
        if not post:
            return jsonify({"success": False, "error": "Post not found"}), 404

        # Check if user has already liked the post
        existing_like = Like.get_by_user_and_post(user_id, post_id)
        
        if existing_like:
            # Unlike the post
            existing_like.delete()
            # Notify the post owner about the unlike (optional)
            if post.user_id != user_id:
                Notification.delete_if_exists(
                    user_id=post.user_id,
                    type='post_like',
                    entity_id=post_id,
                    sender_id=user_id
                )
        else:
            # Like the post
            Like.create(user_id=user_id, post_id=post_id)
            # Notify the post owner about the like
            if post.user_id != user_id:
                Notification.create(
                    user_id=post.user_id,
                    type='post_like',
                    content=f"liked your post",
                    entity_id=post_id,
                    entity_type="post",
                    sender_id=user_id
                )

        return jsonify({"success": True})

    except Exception as e:
        current_app.logger.error(f"Error handling like for post {post_id}: {e}")
        return jsonify({"success": False, "error": "Failed to process like"}), 500

@feed.route("/comment/<int:post_id>", methods=["POST"])
@login_required
def add_comment(post_id):
    """Add a comment to a post."""
    user_id = session.get("user_id")
    content = request.form.get("content")

    if not content:
        return jsonify({
            "success": False,
            "error": "Comment content is required"
        }), 400

    try:
        post = Post.get_by_id(post_id)
        if not post:
            return jsonify({"success": False, "error": "Post not found"}), 404

        comment = Comment.create(
            user_id=user_id,
            post_id=post_id,
            content=content
        )

        if comment and post.user_id != user_id:
            # Notify the post owner about the comment
            Notification.create(
                user_id=post.user_id,
                type='post_comment',
                content=f"commented on your post: {content[:50]}{'...' if len(content) > 50 else ''}",
                entity_id=post_id,
                entity_type="post",
                sender_id=user_id
            )

        return jsonify({
            "success": True,
            "comment": comment.to_dict() if comment else None
        })

    except Exception as e:
        current_app.logger.error(f"Error adding comment to post {post_id}: {e}")
        return jsonify({
            "success": False,
            "error": "Failed to add comment"
        }), 500

@feed.route("/delete_post/<int:post_id>", methods=["DELETE"])
@login_required
def delete_post(post_id):
    """Delete a post."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    try:
        post = Post.get_by_id(post_id) # Assuming Post model has get_by_id

        if not post:
            return jsonify({"error": "Post not found"}), 404

        # Check if the current user is the author of the post
        if post.user_id != user_id:
            return jsonify({"error": "You do not have permission to delete this post"}), 403

        # Assuming a delete method on the model
        post.delete() # Or db.session.delete(post), db.session.commit()

        return jsonify({"message": "Post deleted successfully"})

    except Exception as e:
        current_app.logger.error(f"Error deleting post {post_id} for user {user_id}: {e}")
        return jsonify({"error": "An error occurred"}), 500 