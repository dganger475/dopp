from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify, flash, current_app
from flask_login import login_required, current_user
from models.user import User
from models.user_match import UserMatch
from models.social import Post
from utils.image_paths import normalize_profile_image_path, normalize_extracted_face_path
from datetime import datetime

profile_view = Blueprint('profile_view', __name__)

@profile_view.route("/", methods=["GET"])
@login_required
def view_profile():
    """Show the user's profile.
    
    Returns JSON when request wants JSON (for API/AJAX calls).
    Returns HTML for browser requests.
    """
    user = current_user
    if not user:
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({"success": False, "error": "User not found"}), 404
        flash("User not found", "error")
        return redirect(url_for("main.index"))

    # Check if this is an API/AJAX request (React frontend)
    if request.is_json or request.headers.get('Accept') == 'application/json':
        # Return JSON format for the frontend
        current_app.logger.info(f"Serving JSON profile data for user {user.username}")
        
        # Get basic profile info
        image_url = ""
        
        # Try to get the profile image URL with preference for the get_profile_image_url method
        if hasattr(user, "get_profile_image_url") and callable(getattr(user, "get_profile_image_url")):
            image_url = user.get_profile_image_url()
        elif user.profile_image:
            # Ensure the profile image path is properly formatted
            image_url = normalize_profile_image_path(user.profile_image)
            # Make sure it's a full URL if it's a relative path
            if image_url.startswith('/') and not image_url.startswith('//'):
                image_url = url_for('static', filename=image_url[1:]) if image_url.startswith('/static/') else image_url
        else:
            # Default image
            image_url = url_for('static', filename='images/default_profile.jpg')
        
        # Format dates properly
        join_date = ''
        if user.created_at:
            if hasattr(user.created_at, 'strftime'):
                join_date = user.created_at.strftime('%Y-%m-%d')
            else:
                # Try parsing string to date
                try:
                    join_date = str(user.created_at)[:10]
                except Exception:
                    join_date = datetime.now().strftime('%Y-%m-%d')
        else:
            join_date = datetime.now().strftime('%Y-%m-%d')
        
        # Get cover photo URL with similar logic
        cover_photo = user.cover_photo if hasattr(user, 'cover_photo') else ''
        if cover_photo and cover_photo.startswith('/') and not cover_photo.startswith('//'):
            cover_photo = url_for('static', filename=cover_photo[1:]) if cover_photo.startswith('/static/') else cover_photo
        
        return jsonify({
            "success": True,
            "username": user.username,
            "image": image_url,
            "coverPhoto": cover_photo,
            "bio": user.bio if hasattr(user, 'bio') else '',
            "email": user.email,
            "currentCity": user.current_location_city if hasattr(user, 'current_location_city') else '',
            "state": user.current_location_state if hasattr(user, 'current_location_state') else '',
            "hometown": user.hometown if hasattr(user, 'hometown') else '',
            "memberSince": join_date,
            "fullName": f"{user.first_name} {user.last_name}" if hasattr(user, 'first_name') and hasattr(user, 'last_name') else user.username
        })

    # Regular HTML view for browser requests
    claimed_profiles = user.get_claimed_profiles()
    claimed_profile_count = len(claimed_profiles) if claimed_profiles else 0

    profile_matches = UserMatch.get_by_user_id(user.id, visible_only=True)
    profile_matches = [m for m in profile_matches if getattr(m, "id", None)]

    for match in profile_matches:
        match_details = match.get_match_details() or {}
        if "similarity" not in match_details or match_details.get("similarity") is None:
            match_details["similarity"] = 75.0
            match.update(similarity=75.0)
        match.match_details = match_details
        match.safe_image_path = normalize_extracted_face_path(match.match_filename)

    follower_count = user.get_follower_count()
    match_count = len(profile_matches)
    user_posts = Post.get_user_posts(user.id, limit=10, offset=0)
    user_activities = []
    current_time = datetime.now().strftime("%Y-%m-%d")
    user_image_url = normalize_profile_image_path(user.profile_image)

    if "modern" in request.args or request.args.get("view") == "modern":
        return render_template(
            "social_profile_modern.html",
            user=user,
            claimed_profiles=claimed_profiles,
            matches=profile_matches,
            posts=user_posts,
            follower_count=follower_count,
            match_count=match_count,
            claimed_profile_count=claimed_profile_count,
            user_image_url=user_image_url,
            user_activities=user_activities,
            current_time=current_time,
            is_own_profile=True,
            is_current_user=True,
        )
    return render_template(
        "social_profile.html",
        user=user,
        claimed_profiles=claimed_profiles,
        profile_matches=profile_matches,
        follower_count=follower_count,
        match_count=match_count,
        claimed_profile_count=claimed_profile_count,
        user_activities=user_activities,
        current_time=current_time,
        is_own_profile=True,
        user_image_url=user_image_url,
        is_current_user=True, # Added to fix TypeError
    )

@profile_view.route("/api/user", methods=["GET"])
@login_required
def api_user():
    """Return current user's profile info as JSON for frontend use."""
    user = current_user
    if not user or not user.is_authenticated:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    
    detail = ""
    if user.current_location_city and user.current_location_state:
        detail = f"{user.current_location_city}, {user.current_location_state}"
    elif user.current_location_city:
        detail = user.current_location_city
    elif user.current_location_state:
        detail = user.current_location_state
    elif user.hometown:
        detail = user.hometown
    
    image_url = user.get_profile_image_url() if hasattr(user, "get_profile_image_url") else user.profile_image or "/static/images/default_profile.jpg"
    
    return jsonify({
        "success": True,
        "username": user.username,
        "image": image_url,
        "detail": detail
    })

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