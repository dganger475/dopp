"""
Friends Routes Module
====================

This module contains routes related to managing friends and followers, including:
- Viewing friends, followers, and following
- Following and unfollowing users
- Friend suggestions
"""
import logging
from flask import Blueprint, current_app, jsonify, request, redirect, url_for, flash, session
from flask_login import current_user, login_required # Assuming login_required is here or needs to be imported
from models.user import User # Assuming User model exists
from models.notification import Notification # Assuming Notification model exists

friends = Blueprint('friends', __name__)

# --- Section: Friends and Follows ---
@friends.route("/friends")
@login_required
def view_friends():
    """View friends and follower connections."""
    user_id = session.get("user_id")
    user = User.get_by_id(user_id) # Assuming User model has get_by_id

    if not user:
        flash("User not found", "error")
        return redirect(url_for("main.index")) # Assuming 'main.index' is your application's main route

    # Get friends, followers, and following
    # Assuming User model has these methods
    following = user.get_following()
    followers = user.get_followers()

    # Get friend suggestions
    # Assuming User model has get_friend_suggestions
    suggestions = User.get_friend_suggestions(user_id, limit=5)

    return render_template(
        "friends.html", # Assuming friends.html template exists
        user=user,
        following=following,
        followers=followers,
        suggestions=suggestions,
    )

@friends.route("/follow/<int:user_id>", methods=["POST"])
@login_required
def follow(user_id):
    """Follow a user."""
    current_user_id = session.get("user_id")
    user = User.get_by_id(current_user_id)

    if not user:
        flash("Your account could not be found", "error")
        return redirect(url_for("friends.view_friends")) # Redirect back to friends page

    if current_user_id == user_id:
        flash("You cannot follow yourself", "warning")
        return redirect(url_for("friends.view_friends")) # Redirect back to friends page

    target_user = User.get_by_id(user_id)
    if not target_user:
        flash("User not found", "error")
        return redirect(url_for("friends.view_friends")) # Redirect back to friends page

    # Assuming User model has a follow method
    success = user.follow(user_id)

    if success:
        # Create notification for the followed user
        # Assuming Notification model has create and TYPE_NEW_FOLLOWER
        Notification.create(
            user_id=user_id,
            type=Notification.TYPE_NEW_FOLLOWER if hasattr(Notification, 'TYPE_NEW_FOLLOWER') else 'new_follower',
            content=f"{user.username} started following you", # Assuming user.username is available
            sender_id=current_user_id,
        )

        flash(f"You are now following {target_user.username}", "success")
    else:
        flash("Unable to follow user", "error")

    # Redirect back to the page that initiated the follow action
    referrer = request.referrer
    if referrer and "social/friends" in referrer: # Check if referrer is the friends page
        return redirect(url_for("friends.view_friends"))
    elif referrer:
        return redirect(referrer)
    else:
        return redirect(url_for("social.feed_page")) # Assuming social.feed_page is a fallback

@friends.route("/unfollow/<int:user_id>", methods=["POST"])
@login_required
def unfollow(user_id):
    """Unfollow a user."""
    current_user_id = session.get("user_id")
    user = User.get_by_id(current_user_id)

    if not user:
        flash("Your account could not be found", "error")
        return redirect(url_for("friends.view_friends")) # Redirect back to friends page

    if current_user_id == user_id:
        flash("You cannot unfollow yourself", "warning")
        return redirect(url_for("friends.view_friends")) # Redirect back to friends page

    target_user = User.get_by_id(user_id)
    if not target_user:
        flash("User not found", "error")
        return redirect(url_for("friends.view_friends")) # Redirect back to friends page

    # Assuming User model has an unfollow method
    success = user.unfollow(user_id)

    if success:
        flash(f"You have unfollowed {target_user.username}", "success")
    else:
        flash("Unable to unfollow user", "error")

    # Redirect back to the page that initiated the unfollow action
    referrer = request.referrer
    if referrer and "social/friends" in referrer: # Check if referrer is the friends page
        return redirect(url_for("friends.view_friends"))
    elif referrer:
        return redirect(referrer)
    else:
        return redirect(url_for("social.feed_page")) # Assuming social.feed_page is a fallback 

@friends.route("/invite", methods=["POST"])
@login_required
def send_invites():
    """Send invites to friends (implementation needed)."""
    # TODO: Implement invitation logic
    # This might involve sending emails, generating invite links, etc.
    # Need to get invite details from request.form or request.json
    current_app.logger.info("Send invites route called. Implementation pending.")
    flash("Invite functionality is not yet fully implemented.", "info")
    return redirect(request.referrer or url_for("social.feed_page")) # Redirect back or to a relevant page 