"""
Notifications Blueprint
======================

Handles all notification-related logic for users. Renders notifications.html.
"""

import logging
from datetime import datetime

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from models.social.notification import Notification
from models.social import ClaimedProfile
from models.user import User
from routes.auth import login_required

notifications = Blueprint("notifications", __name__)


@notifications.route("/")
@login_required
def view_notifications():
    """View user notifications."""
    user_id = session.get("user_id")

    # Get the user
    user = User.get_by_id(user_id)
    if not user:
        flash("User not found", "error")
        return redirect(url_for("main.index"))

    # Get notifications with pagination
    page = request.args.get("page", 1, type=int)
    limit = 20
    offset = (page - 1) * limit

    notifications_list = Notification.get_by_user_id(
        user_id, limit=limit, offset=offset
    )

    # Count total unread
    unread_count = Notification.count_unread(user_id)

    return render_template(
        "notifications.html",
        user=user,
        notifications=notifications_list,
        unread_count=unread_count,
        page=page,
    )


@notifications.route("/count_unread")
@login_required
def count_unread_notifications():
    """Get count of unread notifications for current user"""
    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not logged in"}), 401

        unread_count = Notification.query.filter_by(user_id=user_id, read=False).count()

        return jsonify({"count": unread_count})
    except Exception as e:
        current_app.logger.error(f"Error getting unread count: {str(e)}")
        return jsonify({"error": "An error occurred"}), 500


@notifications.route("/mark_read/<int:notification_id>", methods=["POST"])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read."""
    user_id = session.get("user_id")

    # Get the notification
    notification = Notification.get_by_id(notification_id)

    if not notification:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "message": "Notification not found"})
        flash("Notification not found", "error")
        return redirect(url_for("notifications.view_notifications"))

    # Verify ownership
    if notification.user_id != user_id:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(
                {"success": False, "message": "You do not own this notification"}
            )
        flash("You do not own this notification", "error")
        return redirect(url_for("notifications.view_notifications"))

    # Mark as read
    success = notification.mark_as_read()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(
            {
                "success": success,
                "message": (
                    "Notification marked as read"
                    if success
                    else "Error marking notification as read"
                ),
            }
        )

    if success:
        flash("Notification marked as read", "success")
    else:
        flash("Error marking notification as read", "error")

    return redirect(url_for("notifications.view_notifications"))


@notifications.route("/mark_all_read", methods=["POST"])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read."""
    user_id = session.get("user_id")

    # Mark all as read
    success = Notification.mark_all_as_read(user_id)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(
            {
                "success": success,
                "message": (
                    "All notifications marked as read"
                    if success
                    else "Error marking notifications as read"
                ),
            }
        )

    if success:
        flash("All notifications marked as read", "success")
    else:
        flash("Error marking notifications as read", "error")

    return redirect(url_for("notifications.view_notifications"))
