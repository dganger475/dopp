"""
API Blueprint
=============

Provides REST API endpoints for the frontend and mobile apps.
"""

import os

from flask import Blueprint, current_app, jsonify, request, session
from PIL import Image, ImageDraw, ImageFont
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required

from models.face import Face
from models.follow import Follow
from models.user_match import UserMatch
from utils.image_paths import normalize_profile_image_path, resolve_profile_image_path
from utils.search_helpers import get_enriched_faiss_matches
from utils.index.faiss_manager import faiss_index_manager

api = Blueprint("api", __name__)


@api.route("/stats/matches")
@login_required
def get_matches_count():
    """Get the number of matches for the current user."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "Not logged in"})

    # Count user matches
    try:
        # Get all matches (claimed + added)
        from models.social import ClaimedProfile

        # Get claimed profiles
        claimed_profiles = ClaimedProfile.get_by_user_id(user_id)
        claimed_count = len(claimed_profiles) if claimed_profiles else 0

        # Get matches added to profile
        user_matches = UserMatch.get_by_user_id(user_id)
        added_count = len(user_matches) if user_matches else 0

        # Total count (avoid duplicates)
        claimed_filenames = [profile.face_filename for profile in claimed_profiles]
        added_filenames = [match.match_filename for match in user_matches]

        # Combine both sets to avoid duplicates
        all_match_filenames = set(claimed_filenames + added_filenames)
        total_count = len(all_match_filenames)

        current_app.logger.info(f"User {user_id} has {total_count} matches in total")

        return jsonify({"success": True, "count": total_count})
    except Exception as e:
        current_app.logger.error(f"Error getting matches count: {e}")
        return jsonify({"success": False, "message": str(e)})


@api.route("/stats/followers")
@login_required
def get_followers_count():
    """Get the number of followers for the current user."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "Not logged in"})

    # Count followers
    try:
        count = Follow.get_follower_count(user_id)
        return jsonify({"success": True, "count": count})
    except Exception as e:
        current_app.logger.error(f"Error getting followers count: {e}")
        return jsonify({"success": False, "message": str(e)})


@api.route("/stats/following")
@login_required
def get_following_count():
    """Get the number of users the current user is following."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "Not logged in"})

    # Count following
    try:
        count = Follow.get_following_count(user_id)
        return jsonify({"success": True, "count": count})
    except Exception as e:
        current_app.logger.error(f"Error getting following count: {e}")
        return jsonify({"success": False, "message": str(e)})


@api.route("/search", methods=["GET"])
@login_required
def api_search():
    """API endpoint for search queries."""
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    # Sample results for fallback
    sample_results = [
        {
            "username": "@match123",
            "detail": "Los Angeles, CA",
            "image": "/static/images/placeholder.jpg",
            "is_registered": False,
            "similarity": 85,
            "location": "CA 1990s"
        }
    ]

    try:
        if not hasattr(current_user, "profile_image") or not current_user.profile_image:
            return jsonify({
                "results": sample_results,
                "note": "Using sample data (no profile image available)"
            })

        profile_image_fs_path = resolve_profile_image_path(current_user)
        if not profile_image_fs_path or not os.path.exists(profile_image_fs_path):
            return jsonify({
                "results": sample_results,
                "note": "Using sample data (profile image not found)"
            })

        # Get liked faces
        liked_face_ids = UserMatch.get_liked_face_ids_by_user(current_user.id)

        # Perform FAISS search
        enriched_matches, search_error = get_enriched_faiss_matches(
            user_profile_image_fs_path=profile_image_fs_path,
            faiss_index_manager=faiss_index_manager,
            current_user_id=current_user.id,
            liked_face_ids_for_current_user=liked_face_ids,
            top_k=20
        )

        if search_error:
            return jsonify({
                "results": sample_results,
                "note": "Using sample data (search error)",
                "error": search_error
            })

        # Format results for frontend
        frontend_results = []
        for match in enriched_matches:
            frontend_match = {
                "username": f"@{match.get('username') if match.get('username') else 'match' + str(match.get('id', ''))}",
                "detail": match.get('location', ''),
                "image": match.get('image_url') or f"/face/image/{match.get('id', '')}",
                "is_registered": match.get('is_claimed', False),
                "similarity": round(match.get('similarity', 0) * 100),
                "location": f"{match.get('decade', '')} {match.get('location', '')}"
            }
            frontend_results.append(frontend_match)

        return jsonify({"results": frontend_results})

    except Exception as e:
        current_app.logger.error(f"Search error: {str(e)}")
        return jsonify({
            "results": sample_results,
            "note": "Using sample data (error occurred)",
            "error": str(e)
        })


@api.route("/matches/sync", methods=["GET"])
@login_required
def sync_matches():
    """Get matches data for the current user."""
    if not current_user.is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401

    try:
        # Get user matches
        user_matches = UserMatch.get_by_user_id(current_user.id)
        
        # Format matches for response
        matches = []
        for match in user_matches:
            match_data = {
                "id": match.id,
                "filename": match.match_filename,
                "visible": bool(match.is_visible),
                "privacy_level": match.privacy_level,
                "similarity": match.similarity,
                "added_at": match.added_at.isoformat() if match.added_at else None
            }
            matches.append(match_data)

        return jsonify({
            "success": True,
            "matches": matches
        })

    except Exception as e:
        current_app.logger.error(f"Error syncing matches: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api.route("/current_user", methods=["GET"])
@login_required
def api_current_user():
    user = current_user
    if not user or not getattr(user, 'is_authenticated', False):
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    detail = ""
    if hasattr(user, "current_location_city") and hasattr(user, "current_location_state"):
        if user.current_location_city and user.current_location_state:
            detail = f"{user.current_location_city}, {user.current_location_state}"
        elif user.current_location_city:
            detail = user.current_location_city
        elif user.current_location_state:
            detail = user.current_location_state
    if not detail and hasattr(user, "hometown") and user.hometown:
        detail = user.hometown
    if hasattr(user, "get_profile_image_url"):
        image_url = user.get_profile_image_url()
    else:
        image_url = getattr(user, "profile_image", "/static/images/default_profile.jpg")
    return jsonify({
        "success": True,
        "username": getattr(user, "username", "@user"),
        "image": image_url,
        "detail": detail or ""
    })
