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
from models.social.notification import Notification # Needed for share_match

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
    # Get similarity percentage if available
    from models.face import Face
    face = Face.get_by_filename(match_filename)
    similarity = None
    if face:
        # Get the similarity from the face record if available
        similarity = face.similarity if hasattr(face, 'similarity') else None
    
    # Create a clean content string without the filename
    if similarity:
        content = f"I found my historical doppelganger with {int(float(similarity) * 100)}% similarity!"
    else:
        content = "I found my historical doppelganger!"
        
    # Store a reference to the filename but don't include it in the content
    # This way we can still display the image without exposing the filename
    post = Post.create(
        user_id=user_id, 
        content=content, 
        is_match_post=1, 
        face_filename=match_filename  # Still needed for image display
    )
    # Notify original match owner if not current user
    match = UserMatch.get_by_user_and_filename(user_id, match_filename)
    if match and match.user_id != user_id:
        Notification.create(
            user_id=match.user_id,
            type=Notification.TYPE_MATCH_SHARED_TO_FEED,
            content="Your match card was shared to the feed!",
            entity_id=str(post.id),
            entity_type="post",
            sender_id=user_id
        )
    
    # Check if this face is claimed by another user
    from models.face import Face
    face = Face.get_by_filename(match_filename)
    if face and face.claimed_by_user_id and face.claimed_by_user_id != user_id:
        # Notify the user who claimed this face
        Notification.create(
            user_id=face.claimed_by_user_id,
            type=Notification.TYPE_MATCH_SHARED_TO_FEED,
            content="Someone shared a match with your face to the feed!",
            entity_id=str(post.id),
            entity_type="post",
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

from extensions import limiter

@feed.route("/", strict_slashes=False)
@limiter.limit("200 per minute")
@login_required
def feed_page():
    """Display the social feed. Always returns JSON for the React frontend."""
    user_id = session.get("user_id")
    current_app.logger.info(f"Fetching feed for user {user_id}")
    current_app.logger.info(f"Database URI: {current_app.config['SQLALCHEMY_DATABASE_URI']}")

    try:
        posts = Post.get_feed()
        current_app.logger.info(f"Retrieved {len(posts) if posts else 0} posts from database")
        
        if not posts:
            current_app.logger.info("No posts found, creating test post")
            test_post = Post.create(
                user_id=user_id,
                content="Welcome to your social feed! This is a test post."
            )
            if test_post:
                posts = [test_post]
                current_app.logger.info("Test post created successfully")
            else:
                current_app.logger.error("Failed to create test post")

        posts = [post.to_dict(user_id=user_id) for post in posts]
        current_app.logger.info(f"Returning {len(posts)} posts to frontend")
        current_app.logger.debug(f"Posts data: {posts}")

        return jsonify({
            "posts": posts,
            "success": True
        })

    except Exception as e:
        current_app.logger.error(f"Error in feed_page: {str(e)}", exc_info=True)
        return jsonify({
            "success": False,
            "error": "Failed to fetch feed",
            "message": str(e)
        }), 500

@feed.route("/create_post", methods=["POST"])
@login_required
def create_post():
    """Create a new post."""
    user_id = session.get("user_id")
    
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
        content = data.get("content")
        face_filename = data.get("face_filename")
        # Support for match posts from comparison page
        image_url = data.get("image_url")
        if image_url and not face_filename:
            # Extract filename from image_url if provided
            if "/static/faces/" in image_url:
                face_filename = image_url.split("/static/faces/")[-1]
            elif "/static/extracted_faces/" in image_url:
                face_filename = image_url.split("/static/extracted_faces/")[-1]
            else:
                face_filename = image_url  # Use as is if no pattern matches
    else:
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
    current_app.logger.info(f"Like request for post_id={post_id}, user_id={user_id}")
    
    try:
        # Verify post exists
        post = Post.get_by_id(post_id)
        if not post:
            current_app.logger.warning(f"Post not found: {post_id}")
            return jsonify({"success": False, "error": "Post not found"}), 404

        # Check if user has already liked the post
        current_app.logger.info(f"Checking if user {user_id} has already liked post {post_id}")
        existing_like = Like.get_by_user_and_post(user_id, post_id)
        
        likes_count = len(Like.get_by_post(post_id))
        is_liked = False
        
        if existing_like:
            # Unlike the post
            current_app.logger.info(f"User {user_id} already liked post {post_id}, removing like")
            # Use class method directly for more reliability
            Like.delete(post_id, user_id)
            likes_count -= 1
            is_liked = False
            
            # Notify the post owner about the unlike (optional)
            if post.user_id != user_id:
                current_app.logger.info(f"Removing notification for post owner {post.user_id}")
                Notification.delete_if_exists(
                    user_id=post.user_id,
                    type='post_like',
                    entity_id=post_id,
                    sender_id=user_id
                )
        else:
            # Like the post
            current_app.logger.info(f"User {user_id} has not liked post {post_id}, adding like")
            new_like = Like.create(post_id=post_id, user_id=user_id)
            if new_like:
                likes_count += 1
                is_liked = True
                current_app.logger.info(f"Like created successfully for post {post_id}")
                
                # Notify the post owner about the like
                if post.user_id != user_id:
                    current_app.logger.info(f"Creating notification for post owner {post.user_id}")
                    Notification.create(
                        user_id=post.user_id,
                        type=Notification.TYPE_POST_LIKE,
                        content=f"Someone liked your post",
                        entity_id=post_id,
                        entity_type="post",
                        sender_id=user_id
                    )
            else:
                current_app.logger.error(f"Failed to create like for post {post_id}")
                return jsonify({"success": False, "error": "Failed to create like"}), 500

        # Return updated like information
        return jsonify({
            "success": True, 
            "user_has_liked": is_liked,
            "likes_count": likes_count
        })

    except Exception as e:
        import traceback
        current_app.logger.error(f"Error handling like for post {post_id}: {e}")
        current_app.logger.error(traceback.format_exc())
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
                type=Notification.TYPE_POST_COMMENT,
                content=f"Someone commented on your post: {content[:50]}{'...' if len(content) > 50 else ''}",
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