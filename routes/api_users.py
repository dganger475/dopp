"""
API endpoints for user data in the DoppleGänger app.
"""

import logging
from flask import Blueprint, jsonify, session
from utils.image_paths import normalize_profile_image_path
from models.user import User

# Create blueprint
api_users = Blueprint("api_users", __name__)

@api_users.route("/users/current")
def get_current_user():
    """Get current user data for frontend"""
    logging.info('[api_users] get_current_user endpoint called')
    
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "Not logged in"}), 401
    
    # Get user data using the User model
    user = User.get_by_id(user_id)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # Format user data for response
    user_data = {
        "id": user.id,
        "username": user.username,
        "profile_image": user.profile_image,
        "profile_image_url": normalize_profile_image_path(user.profile_image),
        "email": user.email,
        "bio": user.bio,
        "current_location_city": user.current_location_city,
        "current_location_state": user.current_location_state,
        "hometown": user.hometown,
        "created_at": user.created_at
    }
    
    return jsonify({"success": True, "user": user_data})
