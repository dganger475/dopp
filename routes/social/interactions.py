"""
Interactions Routes Module
========================

This module contains routes related to post interactions, including:
- Likes and reactions
- Comments
- Sharing
"""
import logging
from flask import Blueprint, current_app, jsonify, request, redirect, url_for, flash, session
from flask_login import current_user, login_required
from models.social import Like, Comment, Post, Notification

interactions = Blueprint('interactions', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Section: Post Interaction Routes ---

@interactions.route("/like_post/<int:post_id>", methods=["POST"])
@login_required
def like_post(post_id):
    """Like or unlike a post."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    try:
        # Check if the like exists
        existing_like = Like.query.filter_by(user_id=user_id, post_id=post_id).first() # Assuming SQLAlchemy syntax

        if existing_like:
            # Unlike the post
            # Assuming a delete method on the model
            existing_like.delete() # Or db.session.delete(existing_like), db.session.commit()
            is_liked = False
            message = "Post unliked"
        else:
            # Like the post
            new_like = Like.create(user_id=user_id, post_id=post_id) # Assuming Like.create method
            if new_like:
                is_liked = True
                message = "Post liked"

                # Optional: Notify post owner
                post = Post.get_by_id(post_id) # Assuming Post model has get_by_id
                if post and post.user_id != user_id:
                     Notification.create(
                        user_id=post.user_id,
                        type=Notification.TYPE_NEW_LIKE if hasattr(Notification, 'TYPE_NEW_LIKE') else 'new_like',
                        content=f"{current_user.username} liked your post", # Assuming current_user is available from Flask-Login
                        entity_id=post_id,
                        entity_type="post",
                        sender_id=user_id
                    )
            else:
                return jsonify({"error": "Failed to like post"}), 500

        # Assuming this is an AJAX endpoint, return JSON
        return jsonify({"message": message, "is_liked": is_liked})

    except Exception as e:
        logger.error(f"Error liking/unliking post {post_id} for user {user_id}: {e}")
        return jsonify({"error": "An error occurred"}), 500

@interactions.route("/add_comment/<int:post_id>", methods=["POST"])
@login_required
def add_comment(post_id):
    """Add a comment to a post."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    content = request.form.get("comment_content") # Assuming form data

    if not content:
        flash("Comment content cannot be empty", "warning")
        # Assuming a redirect back to the feed or post view
        return redirect(request.referrer or url_for("social.feed_page"))

    try:
        # Assuming Comment.create method
        comment = Comment.create(user_id=user_id, post_id=post_id, content=content)

        if comment:
            # Optional: Notify post owner
            post = Post.get_by_id(post_id)
            if post and post.user_id != user_id:
                 Notification.create(
                    user_id=post.user_id,
                    type=Notification.TYPE_NEW_COMMENT if hasattr(Notification, 'TYPE_NEW_COMMENT') else 'new_comment',
                    content=f"{current_user.username} commented on your post",
                    entity_id=post_id,
                    entity_type="post",
                    sender_id=user_id
                )

            flash("Comment added successfully!", "success")
        else:
            flash("Error adding comment.", "error")

    except Exception as e:
        logger.error(f"Error adding comment to post {post_id} for user {user_id}: {e}")
        flash("An error occurred while adding your comment.", "error")

    # Assuming a redirect back to the feed or post view
    return redirect(request.referrer or url_for("social.feed_page"))

@interactions.route("/delete_comment/<int:comment_id>", methods=["POST", "DELETE"])
@login_required
def delete_comment(comment_id):
    """Delete a comment."""
    user_id = session.get("user_id")
    if not user_id:
        # Assuming AJAX for DELETE or form submission for POST
        if request.method == "DELETE":
             return jsonify({"error": "User not logged in"}), 401
        else:
            flash("User not logged in", "error")
            return redirect(request.referrer or url_for("social.feed_page"))

    try:
        comment = Comment.get_by_id(comment_id) # Assuming Comment model has get_by_id

        if not comment:
            if request.method == "DELETE":
                return jsonify({"error": "Comment not found"}), 404
            else:
                flash("Comment not found", "error")
                return redirect(request.referrer or url_for("social.feed_page"))

        # Check if the current user is the author of the comment or the post owner
        post = Post.get_by_id(comment.post_id) # Assuming Post model has get_by_id
        if comment.user_id != user_id and (not post or post.user_id != user_id):
             if request.method == "DELETE":
                return jsonify({"error": "You do not have permission to delete this comment"}), 403
             else:
                flash("You do not have permission to delete this comment", "error")
                return redirect(request.referrer or url_for("social.feed_page"))

        # Assuming a delete method on the model
        comment.delete() # Or db.session.delete(comment), db.session.commit()

        if request.method == "DELETE":
            return jsonify({"message": "Comment deleted successfully"})
        else:
            flash("Comment deleted successfully!", "success")
            return redirect(request.referrer or url_for("social.feed_page"))

    except Exception as e:
        logger.error(f"Error deleting comment {comment_id} for user {user_id}: {e}")
        if request.method == "DELETE":
             return jsonify({"error": "An error occurred"}), 500
        else:
            flash("An error occurred while deleting the comment.", "error")
            return redirect(request.referrer or url_for("social.feed_page"))

@interactions.route("/share/comparison", methods=["POST"])
@login_required
def share_comparison():
    """Share a comparison result to the feed."""
    user_id = session.get("user_id")
    comparison_id = request.form.get("comparison_id") # Assuming comparison_id is passed

    if not comparison_id:
        flash("Comparison ID is missing", "warning")
        return redirect(request.referrer or url_for("social.feed_page")) # Redirect back

    try:
        # TODO: Validate comparison_id and retrieve comparison details
        # TODO: Create a post type specific to comparisons
        content = f"Check out my comparison result! [Comparison ID: {comparison_id}]"
        # Assuming Post.create can handle a comparison type or reference
        post = Post.create(user_id=user_id, content=content, entity_type="comparison", entity_id=comparison_id)

        if post:
            flash("Comparison shared to feed!", "success")
        else:
            flash("Error sharing comparison.", "error")

    except Exception as e:
        logger.error(f"Error sharing comparison {comparison_id} for user {user_id}: {e}")
        flash("An error occurred while sharing the comparison.", "error")

    return redirect(request.referrer or url_for("social.feed_page"))

@interactions.route("/share_claimed_profile/<filename>", methods=["POST"])
@login_required
def share_claimed_profile(filename):
    """Share a claimed profile to the feed."""
    user_id = session.get("user_id")

    if not filename:
        flash("Filename is missing", "warning")
        return redirect(request.referrer or url_for("social.feed_page")) # Redirect back

    try:
        # TODO: Verify the user has claimed this profile/filename
        # TODO: Create a post type specific to claimed profiles
        content = f"I've claimed a new historical profile! [Profile: {filename}]"
         # Assuming Post.create can handle a claimed profile type or reference
        post = Post.create(user_id=user_id, content=content, entity_type="claimed_profile", face_filename=filename)

        if post:
            flash("Claimed profile shared to feed!", "success")

            # Optional: Notify original claimer if different user (though unlikely for claiming)
            claimed_profile = ClaimedProfile.get_by_filename(filename) # Assuming ClaimedProfile model exists
            if claimed_profile and claimed_profile.user_id != user_id:
                 Notification.create(
                    user_id=claimed_profile.user_id,
                    type=Notification.TYPE_PROFILE_SHARED if hasattr(Notification, 'TYPE_PROFILE_SHARED') else 'profile_shared',
                    content=f"{current_user.username} shared a profile you claimed",
                    entity_id=claimed_profile.id, # Or filename
                    entity_type="claimed_profile",
                    sender_id=user_id
                )

        else:
            flash("Error sharing claimed profile.", "error")

    except Exception as e:
        logger.error(f"Error sharing claimed profile {filename} for user {user_id}: {e}")
        flash("An error occurred while sharing the claimed profile.", "error")

    return redirect(request.referrer or url_for("social.feed_page"))