"""Notification routes for DoppleGänger
====================================

This module defines the notification routes for the application.
"""

import logging
from flask import Blueprint, jsonify, request, current_app
from models.social import Notification

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications', methods=['GET'])
def get_notifications():
    """Get notifications for a user."""
    try:
        user_id = request.args.get('user_id')
        notifications = Notification.get_by_user_id(user_id)
        return jsonify([notification.to_dict() for notification in notifications])
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return jsonify({"error": str(e)}), 500

@notifications_bp.route('/notifications/<int:notification_id>', methods=['PUT'])
def mark_notification_as_read(notification_id):
    """Mark a notification as read."""
    try:
        notification = Notification.get_by_id(notification_id)
        if notification:
            notification.mark_as_read()
        return jsonify(notification.to_dict())
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        return jsonify({"error": str(e)}), 500

@notifications_bp.route('/notifications/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Delete a notification."""
    try:
        notification = Notification.get_by_id(notification_id)
        if notification:
            notification.delete()
        return jsonify({"message": "Notification deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting notification: {e}")
        return jsonify({"error": str(e)}), 500
