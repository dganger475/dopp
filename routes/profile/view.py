from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify, flash, current_app
from flask_login import login_required, current_user
from models.user import User
from models.user_match import UserMatch
from models.social import Post
from utils.image_paths import normalize_profile_image_path, normalize_extracted_face_path
from datetime import datetime

# Create blueprint with url_prefix='/profile' to handle routing correctly
profile_view = Blueprint('profile_view', __name__, url_prefix='/profile')

@profile_view.route("/", methods=["GET"])  # Main route with trailing slash
@login_required
def view_profile():
    """Show the user's profile.
    Returns JSON when requested with Accept: application/json header or ?format=json parameter
    Otherwise returns HTML template for direct browser access
    """
    user = current_user
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404
        
    # Always return JSON as this is a React SPA
    # No template rendering needed since React handles the UI
    
    current_app.logger.info(f"Serving JSON profile data for user {user.username}")
    
    # === Process Profile Image URL ===
    image_url = ""
    
    if hasattr(user, "get_profile_image_url") and callable(getattr(user, "get_profile_image_url")):
        image_url = user.get_profile_image_url()
    elif user.profile_image:
        image_url = normalize_profile_image_path(user.profile_image)
        if image_url.startswith('/') and not image_url.startswith('//'):
            image_url = url_for('static', filename=image_url[1:]) if image_url.startswith('/static/') else image_url
    # No default image fallback - React will handle missing images
    
    # === Format Join Date ===
    join_date = ''
    if user.created_at:
        if hasattr(user.created_at, 'strftime'):
            join_date = user.created_at.strftime('%Y-%m-%d')
        else:
            try:
                join_date = str(user.created_at)[:10]
            except Exception:
                join_date = datetime.now().strftime('%Y-%m-%d')
    else:
        join_date = datetime.now().strftime('%Y-%m-%d')
    
    # === Process Cover Photo ===
    cover_photo = user.cover_photo if hasattr(user, 'cover_photo') else ''
    if cover_photo and cover_photo.startswith('/') and not cover_photo.startswith('//'):
        cover_photo = url_for('static', filename=cover_photo[1:]) if cover_photo.startswith('/static/') else cover_photo

    # === Get Related User Data ===
    claimed_profiles = user.get_claimed_profiles()
    claimed_profile_count = len(claimed_profiles) if claimed_profiles else 0

    # Get matches but NEVER use default images for face matching
    profile_matches = UserMatch.get_by_user_id(user.id, visible_only=True)
    profile_matches = [m for m in profile_matches if getattr(m, "id", None)]
    match_count = len(profile_matches)
    follower_count = user.get_follower_count()

    # Process match details - NO default images for face matching
    processed_matches = []
    for match in profile_matches:
        match_details = match.get_match_details() or {}
        if "similarity" not in match_details or match_details.get("similarity") is None:
            match_details["similarity"] = 75.0
            match.update(similarity=75.0)
            
        # Use actual face image path - NEVER use default placeholder images
        image_path = normalize_extracted_face_path(match.match_filename)
        
        processed_matches.append({
            "id": match.id,
            "image_path": image_path,
            "similarity": match_details.get("similarity", 75.0),
            "details": match_details
        })

    # === Create Full JSON Response with all necessary fields for the profile page ===
    # Make sure to include all fields needed by the frontend in the exact format it expects
    response_data = {
        "success": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "image": image_url,
            "profile_image_url": image_url,  # Add this for frontend compatibility
            "coverPhoto": cover_photo,
            "bio": user.bio if hasattr(user, 'bio') else '',
            "email": user.email,
            "current_city": user.current_location_city if hasattr(user, 'current_location_city') else '',  # Add this for frontend compatibility
            "current_location_city": user.current_location_city if hasattr(user, 'current_location_city') else '',
            "current_location_state": user.current_location_state if hasattr(user, 'current_location_state') else '',
            "hometown": user.hometown if hasattr(user, 'hometown') else '',
            "memberSince": join_date,  # This is the field used by the frontend
            "created_at": join_date,  # Include both formats for compatibility
            "full_name": f"{user.first_name} {user.last_name}" if hasattr(user, 'first_name') and hasattr(user, 'last_name') else user.username
        },
        "claimed_profiles": [profile.to_dict() if hasattr(profile, 'to_dict') else {"id": profile.id} for profile in claimed_profiles] if claimed_profiles else [],
        "matches": processed_matches,
        "follower_count": follower_count,
        "match_count": match_count,
        "claimed_profile_count": claimed_profile_count,
        "is_own_profile": True
    }
    
    # Log the response data for debugging
    current_app.logger.info(f"Profile response data: {response_data}")
    
    return jsonify(response_data)

@profile_view.route("/api/user", methods=["GET"])
@login_required
def api_user():
    """Return current user's profile info as JSON for frontend use."""
    user = current_user
    if not user or not user.is_authenticated:
        response = jsonify({"success": False, "error": "Not authenticated"})
        origin = request.headers.get('Origin')
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response, 401
    
    # Format join date
    join_date = ''
    if user.created_at:
        if hasattr(user.created_at, 'strftime'):
            join_date = user.created_at.strftime('%Y-%m-%d')
        else:
            try:
                join_date = str(user.created_at)[:10]
            except Exception:
                join_date = datetime.now().strftime('%Y-%m-%d')
    else:
        join_date = datetime.now().strftime('%Y-%m-%d')
    
    # Get profile image URL
    image_url = user.get_profile_image_url()
    current_app.logger.info(f"[api_user] Returning profile_image_url: {image_url} for user {user.id} ({user.username})")
    
    # Get cover photo URL
    cover_photo = user.cover_photo_url
    
    # Create comprehensive user data with consistent structure
    user_data = {
        "id": user.id,
        "username": user.username,
        "profile_image_url": image_url,
        "coverPhoto": cover_photo,
        "bio": user.bio if hasattr(user, 'bio') else '',
        "email": user.email,
        "current_city": user.current_location_city if hasattr(user, 'current_location_city') else '',
        "current_location_city": user.current_location_city if hasattr(user, 'current_location_city') else '',
        "current_location_state": user.current_location_state if hasattr(user, 'current_location_state') else '',
        "hometown": user.hometown if hasattr(user, 'hometown') else '',
        "memberSince": join_date,
        "full_name": f"{user.first_name} {user.last_name}".strip() if hasattr(user, 'first_name') and hasattr(user, 'last_name') and (user.first_name or user.last_name) else user.username
    }
    
    current_app.logger.info(f"[api_user] User data: {user_data}")
    response = jsonify(user_data)
    origin = request.headers.get('Origin')
    if origin:
        response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

# Alias: /profile/ returns the same as /profile/api/user
@profile_view.route("/", methods=["GET"])
@login_required
def api_user_alias():
    """Return current user's profile info as JSON for frontend use."""
    return api_user()

@profile_view.route("/mobile_profile")
def mobile_profile():
    """Demo mobile profile endpoint for previewing a user profile on mobile UI."""
    user = {
        "name": "Alex Johnson",
        "image_url": "/static/images/example.jpg",
        "hometown": "Seattle, WA",
        "birthday": "April 15, 1990",
        "decade": "1980s",
        "state": "NY",
        "bio": "A creative spirit with a passion for connecting with new faces and exploring the world through different perspectives.",
    }
    return render_template("mobile_profile.html", user=user)