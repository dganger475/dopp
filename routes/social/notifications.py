"""
Notifications Routes Module
========================

This module contains routes related to notifications, including:
- Notification retrieval
- Notification status updates
- Notification preferences
"""
from flask import Blueprint, current_app, jsonify, request, session
from flask_login import current_user, login_required
# from flask_limiter import Limiter # Not used in current routes
# from flask_limiter.util import get_remote_address # Not used in current routes
# from datetime import datetime # Not used in current routes
from models.social.notification import Notification

notifications = Blueprint('notifications', __name__)

@notifications.route('/', methods=['GET'])
@login_required
def get_notifications():
    """Get user's notifications with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    try:
        # Get notifications from database
        notifications_list = get_paginated_notifications(page, per_page)
        return jsonify({
            'notifications': notifications_list,
            'has_more': len(notifications_list) == per_page
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching notifications: {e}")
        return jsonify({'error': 'Failed to fetch notifications'}), 500

@notifications.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_as_read(notification_id):
    """Mark a notification as read."""
    try:
        # Update notification status in database
        success = mark_notification_read(notification_id)
        
        if success:
            return jsonify({'message': 'Notification marked as read'})
        else:
            return jsonify({'error': 'Notification not found'}), 404
    except Exception as e:
        current_app.logger.error(f"Error marking notification as read: {e}")
        return jsonify({'error': 'Failed to mark notification as read'}), 500

@notifications.route('/mark_all_read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all notifications as read."""
    try:
        from models.social.notification import Notification
        from flask import session
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        # Mark all notifications as read
        count = Notification.mark_all_as_read(user_id)
        
        return jsonify({
            'message': f'{count} notifications marked as read',
            'count': count
        })
    except Exception as e:
        current_app.logger.error(f"Error marking all notifications as read: {e}")
        return jsonify({'error': 'Failed to mark all notifications as read'}), 500

@notifications.route('/unread_count', methods=['GET'])
@login_required
def get_unread_count():
    """Get the count of unread notifications for the current user."""
    try:
        from models.social.notification import Notification
        from flask import session
        
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'User not authenticated'}), 401
            
        # Get the count of unread notifications
        count = Notification.count_unread(user_id)
        
        return jsonify({
            'count': count
        })
    except Exception as e:
        current_app.logger.error(f"Error getting unread notification count: {e}")
        return jsonify({'error': 'Failed to get unread notification count'}), 500

@notifications.route('/preferences', methods=['GET', 'POST'])
@login_required
def notification_preferences():
    """Get or update notification preferences."""
    if request.method == 'GET':
        try:
            preferences = get_notification_preferences()
            return jsonify(preferences)
        except Exception as e:
            current_app.logger.error(f"Error fetching notification preferences: {e}")
            return jsonify({'error': 'Failed to fetch notification preferences'}), 500
    else:
        try:
            data = request.get_json()
            success = update_notification_preferences(data)
            
            if success:
                return jsonify({'message': 'Notification preferences updated'})
            else:
                return jsonify({'error': 'Invalid preferences'}), 400
        except Exception as e:
            current_app.logger.error(f"Error updating notification preferences: {e}")
            return jsonify({'error': 'Failed to update notification preferences'}), 500

def get_paginated_notifications(page, per_page):
    """Helper function to get paginated notifications from database."""
    from models.social.notification import Notification
    from models.user import User
    
    user_id = session.get('user_id')
    if not user_id:
        return []
        
    # Calculate offset based on page and per_page
    offset = (page - 1) * per_page
    
    # Get notifications from database with pagination
    notifications = Notification.get_by_user_id(
        user_id=user_id,
        limit=per_page,
        offset=offset
    )
    
    # Format notifications for JSON response
    formatted_notifications = []
    for notif in notifications:
        # Get sender information if available
        sender_info = None
        if notif.sender_id:
            sender = User.get_by_id(notif.sender_id)
            if sender:
                sender_info = {
                    'id': sender.id,
                    'username': sender.username,
                    'profile_image': sender.profile_image
                }
        
        # Format notification
        formatted_notification = {
            'id': notif.id,
            'type': notif.type,
            'content': notif.content,
            'entity_id': notif.entity_id,
            'entity_type': notif.entity_type,
            'is_read': bool(notif.is_read),
            'created_at': notif.created_at,
            'sender': sender_info
        }
        
        formatted_notifications.append(formatted_notification)
    
    return formatted_notifications

def mark_notification_read(notification_id):
    """Helper function to mark notification as read in database."""
    from models.social.notification import Notification
    from flask import session
    
    user_id = session.get('user_id')
    if not user_id:
        return False
        
    # Get the notification from the database
    notification = Notification.get_by_id(notification_id)
    
    # Check if the notification exists and belongs to the current user
    if not notification or notification.user_id != user_id:
        return False
        
    # Mark the notification as read
    return notification.mark_as_read()

def get_notification_preferences():
    """Helper function to get notification preferences from database."""
    # TODO: Implement database query
    return {}

def update_notification_preferences(preferences):
    """Helper function to update notification preferences in database."""
    # TODO: Implement database update
    return True 