"""
CORS Proxy Routes
================

Special routes that handle CORS properly, especially for authentication.
These routes bypass normal middleware to ensure OPTIONS requests work correctly.
"""
from flask import Blueprint, jsonify, request, session, current_app
import os

# Create a blueprint that won't use typical middleware
cors_proxy = Blueprint('cors_proxy', __name__)

@cors_proxy.route("/auth_status", methods=["GET", "OPTIONS"])
def auth_status():
    """Check authentication status with proper CORS handling.
    This is a direct endpoint that bypasses normal middleware."""
    
    # For OPTIONS requests, return immediate 200 OK with CORS headers
    if request.method == "OPTIONS":
        response = jsonify({"status": "preflight_ok"})
        origin = request.headers.get('Origin', '*')
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Cache-Control, X-Csrf-Token, X-CSRFToken'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Max-Age'] = '86400'  # 24 hours
        return response
    
    # Process GET request - directly check session without using login_required
    user_id = session.get('user_id')
    authenticated = False
    user_data = {}
    
    if user_id:
        # Direct database query to check user exists
        from models.user import User
        user = User.get_by_id(user_id)
        
        if user:
            authenticated = True
            
            # Get profile image - being careful to follow requirements about NOT using defaults for search
            profile_image_url = None
            
            # First check user's profile image
            if hasattr(user, 'profile_image') and user.profile_image:
                profile_image_url = f"/static/profile_pics/{user.profile_image}"
                # Make it a full URL if needed
                if request.host:
                    if not profile_image_url.startswith('http'):
                        host = request.host_url.rstrip('/')
                        profile_image_url = f"{host}{profile_image_url}"
            
            # If no profile image in user table, check faces table for claimed faces
            if not profile_image_url:
                try:
                    from models.face import Face
                    face = Face.get_claimed_by_user(user_id)
                    if face and hasattr(face, 'filename') and face.filename:
                        face_url = f"/static/faces/{face.filename}"
                        if request.host:
                            if not face_url.startswith('http'):
                                host = request.host_url.rstrip('/')
                                face_url = f"{host}{face_url}"
                        profile_image_url = face_url
                except Exception as e:
                    current_app.logger.error(f"Error getting claimed face: {str(e)}")
            
            # Build user data response
            user_data = {
                "id": user.id,
                "username": user.username,
                "profile_image_url": profile_image_url
            }
            
            # Add additional fields if they exist
            if hasattr(user, 'email'):
                user_data["email"] = user.email
                
            if hasattr(user, 'first_name') and hasattr(user, 'last_name'):
                user_data["first_name"] = user.first_name
                user_data["last_name"] = user.last_name
    
    # Build response
    response_data = {
        "authenticated": authenticated,
        "success": authenticated,
    }
    
    # Only include user data if authenticated
    if authenticated:
        response_data["user"] = user_data
    
    # Create response with CORS headers
    response = jsonify(response_data)
    origin = request.headers.get('Origin')
    if origin:
        response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    
    return response
