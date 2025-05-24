import json
import logging
import math
import os
import random
import time

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
    Response,
)
from flask_login import current_user, login_required
import face_recognition
import numpy as np

from models.face import Face
from models.social import ClaimedProfile, Post
from models.sqlalchemy_models import db
from models.user import User
from models.user_match import UserMatch
from routes.auth import login_required
from utils.db.database import get_db_connection, get_users_db_connection
from utils.face.metadata import enhance_face_with_metadata, get_metadata_for_face
from utils.image_paths import normalize_profile_image_path
from utils.index.faiss_manager import faiss_index_manager
from utils.search_helpers import (
    apply_privacy_filters,
    get_enriched_faiss_matches,
    perform_text_search,
    resolve_profile_image_path,
)
from utils.face.recognition import extract_face_encoding, find_similar_faces_faiss, calculate_similarity
from models.user_match import UserMatch

search_bp = Blueprint("search", __name__)


@search_bp.route("/", methods=["GET"])
@login_required
def search_page():
    """Display the search page."""
    return render_template("search.html")


@search_bp.route("/api/search", methods=["GET"])
def api_search():
    """API endpoint for finding lookalikes using face similarity search (FAISS and registered users)."""
    current_app.logger.info("[SEARCH] API search endpoint called")

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not authenticated", "success": False}), 401

    user = User.get_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found", "success": False}), 401

    if not hasattr(user, "profile_image") or not user.profile_image or \
       user.profile_image in ['default_profile.png', 'default.png', 'default.jpg'] or \
       'default' in user.profile_image.lower():
        return jsonify({
            "error": "Valid profile image required",
            "message": "Please upload your own clear face photo to find your historical lookalikes. Default images cannot be used.",
            "results": [], "total": 0, "success": False
        }), 400

    try:
        profile_image_fs_path = resolve_profile_image_path(user)
        if not profile_image_fs_path or not os.path.exists(profile_image_fs_path):
            return jsonify({
                "error": "Profile image not found on server",
                "message": "Could not locate your profile image. Please try uploading it again.",
                "results": [], "total": 0, "success": False
            }), 400

        image = face_recognition.load_image_file(profile_image_fs_path)
        face_locations = face_recognition.face_locations(image)
        if not face_locations:
            return jsonify({
                "error": "No face detected in profile image",
                "message": "Could not detect a face in your profile image. Please upload a clear face photo.",
                "results": [], "total": 0, "success": False
            }), 400
        current_user_face_encoding = face_recognition.face_encodings(image, face_locations)[0]

        # 1. Fetch FAISS matches (historical photos)
        faiss_results_formatted = []
        try:
            liked_face_ids = UserMatch.get_liked_face_ids_by_user(user.id)
            faiss_matches_raw, faiss_error = get_enriched_faiss_matches(
                user_profile_image_fs_path=profile_image_fs_path,
                faiss_index_manager=faiss_index_manager,
                current_user_id=user.id,
                liked_face_ids_for_current_user=liked_face_ids,
                top_k=50
            )
            if faiss_error:
                current_app.logger.error(f"[SEARCH] Error fetching FAISS matches: {faiss_error}")
            if faiss_matches_raw:
                for fm_raw in faiss_matches_raw:
                    # Get the image URL from the FAISS match - use safe_image_path first if available
                    image_url = fm_raw.get('safe_image_path', '')
                    if not image_url:
                        image_url = fm_raw.get('image_url', '')
                    
                    # Fallback if still no image URL
                    if not image_url or not image_url.startswith(('/static/', 'http')):
                        image_url = f"/static/faces/{fm_raw.get('filename', '')}"
                    
                    # Log the image path we're using
                    current_app.logger.debug(f"[SEARCH] Using image URL for FAISS match: {image_url}")
                    
                    # Generate a privacy-safe ID for unregistered users based on index or filename hash
                    face_id = fm_raw.get('id') or (hash(fm_raw.get('filename', '')) % 10000000)
                    
                    # Determine if this is a registered user (has claimed user data)
                    is_registered = bool(fm_raw.get('claimed_by_user_id'))
                    
                    # Use a privacy-safe username for unregistered users
                    # Only use actual username for registered users
                    if is_registered:
                        display_username = fm_raw.get('claimed_by_username') or fm_raw.get('claimant_username') or 'Registered User'
                    else:
                        # Privacy-safe alternative - use ID + decade if available
                        decade_text = fm_raw.get('decade', '')
                        state_text = fm_raw.get('state', '')
                        location_text = ''
                        
                        if decade_text and state_text:
                            location_text = f"{state_text}, {decade_text}"
                        elif decade_text:
                            location_text = decade_text
                        elif state_text:
                            location_text = state_text
                            
                        display_username = f"Profile #{face_id}" if not location_text else f"Profile #{face_id} ({location_text})"
                    
                    # Determine data source for tracking
                    # If filename starts with userprofile_, it's from users table; otherwise, it's from faces table
                    filename_str = fm_raw.get('filename', '')
                    data_source = "users_table" if filename_str.startswith("userprofile_") else "faces_table"
                    
                    # If the filename indicates this is a user profile, it should be marked as registered
                    if filename_str.startswith("userprofile_"):
                        is_registered = True
                        current_app.logger.debug(f"[SEARCH] Identified user profile from filename: {filename_str}")
                    
                    # Format the result consistently with registered users
                    faiss_results_formatted.append({
                        "id": f"face_{face_id}",
                        "username": display_username,
                        "image": image_url,
                        "safe_image_path": image_url,  # Add this for consistency
                        "decade": fm_raw.get('decade', ''),
                        "state": fm_raw.get('state', ''),
                        "similarity": float(fm_raw.get('similarity', 0)),  # Already in 0-1 scale from get_enriched_faiss_matches
                        "is_registered": is_registered,
                        "is_historical": True,
                        "location": fm_raw.get('state', '') or fm_raw.get('school_name', ''),
                        "claimed_by_user_id": fm_raw.get('claimed_by_user_id'),
                        "original_filename": fm_raw.get('filename'), # Keep this for internal use, not displayed to users
                        "data_source": data_source  # Track which table this came from
                    })
        except Exception as e_faiss:
            current_app.logger.error(f"[SEARCH] Exception during FAISS search: {str(e_faiss)}")

        # 2. Fetch Registered User Matches
        registered_user_results_formatted = []
        conn_users = None
        try:
            conn_users = get_users_db_connection()
            cursor = conn_users.cursor()
            cursor.execute("""
                SELECT u.id, u.username, u.profile_image, u.face_encoding, u.current_location_city, u.current_location_state
                FROM users u WHERE u.id != ? AND u.face_encoding IS NOT NULL AND u.profile_image IS NOT NULL
                AND u.profile_image NOT LIKE '%default%' AND u.profile_image != ''
            """, (user.id,))
            other_users = cursor.fetchall()
            for other_user_row in other_users:
                other_user_id, other_username, other_profile_image, other_encoding_blob, other_city, other_state = other_user_row
                if other_encoding_blob:
                    try:
                        # Properly handle the face encoding comparison
                        other_user_encoding = np.frombuffer(other_encoding_blob, dtype=np.float64)
                        distance = np.linalg.norm(current_user_face_encoding - other_user_encoding)
                        
                        # Calculate actual true percentage similarity using the same method as FAISS
                        # Using the standard face recognition threshold of 0.6
                        similarity_score = calculate_similarity(distance) # Returns 0-100 percentage
                        
                        # Construct a proper image URL based on the profile_image path
                        if other_profile_image.startswith('userprofile_'):
                            image_url = f"/static/faces/{other_profile_image}"
                        elif other_profile_image.startswith('/static/'):
                            image_url = other_profile_image
                        elif other_profile_image.startswith('static/'):
                            image_url = f"/{other_profile_image}"
                        else:
                            # Try multiple possible locations
                            potential_paths = [
                                f"/static/profile_pics/{other_profile_image}",
                                f"/static/faces/{other_profile_image}",
                                f"/static/{other_profile_image}"
                            ]
                            
                            # Check which one exists
                            image_url = potential_paths[0]  # Default
                            for path in potential_paths:
                                full_path = os.path.join(current_app.root_path, 'static', path.replace('/static/', ''))
                                if os.path.exists(full_path):
                                    image_url = path
                                    break
                        
                        # Don't filter based on similarity yet - include all and sort later
                        # These are ALWAYS registered users since they come from the users table
                        registered_user_results_formatted.append({
                            "id": f"user_{other_user_id}",
                            "username": other_username,
                            "image": image_url,
                            "safe_image_path": image_url,  # Add this for consistency with FAISS results
                            "decade": "",
                            "state": other_state or "",
                            "similarity": float(similarity_score) / 100,  # Convert to 0-1 scale for consistent frontend display
                            "is_registered": True,  # Explicitly mark as registered
                            "is_historical": False,
                            "location": f"{other_city}, {other_state}" if other_city and other_state else (other_city or other_state or ""),
                            "registered_user_id": other_user_id,
                            "data_source": "users_table"  # Track data source
                        })
                        current_app.logger.debug(f"[SEARCH] Registered user match found: {other_username} with similarity {similarity_score}")
                    except Exception as e_encoding:
                        current_app.logger.error(f"[SEARCH] Error processing encoding for user {other_user_id}: {str(e_encoding)}")
                        continue
        except Exception as e_users_search:
            current_app.logger.error(f"[SEARCH] Exception during registered users search: {str(e_users_search)}")
        finally:
            if conn_users: conn_users.close()

        # 3. Combine and Deduplicate
        # Add debug output for original results before combining
        current_app.logger.debug(f"FAISS results count: {len(faiss_results_formatted)}, Registered users count: {len(registered_user_results_formatted)}")
        for i, reg_user in enumerate(registered_user_results_formatted):
            current_app.logger.debug(f"Registered user {i} - is_registered: {reg_user.get('is_registered', False)}, username: {reg_user.get('username')}")
            
        # Combine results and set up deduplication
        all_results_combined = faiss_results_formatted + registered_user_results_formatted
        final_results_map = {}
        
        for item in all_results_combined:
            key = None
            
            # Flag to track if this is a registered user (either directly or via claiming)
            is_registered_user = False
            
            # Prioritize registered user profiles if a historical photo is claimed by them
            if item.get('is_historical') and item.get('claimed_by_user_id'):
                key = f"user_{item['claimed_by_user_id']}"
                is_registered_user = True  # This is a claimed profile (registered user)
            elif item.get('is_registered') and not item.get('is_historical'):
                key = f"user_{item['registered_user_id']}"
                is_registered_user = True  # This is a direct registered user match
            elif item.get('is_historical'): # Unclaimed historical photo
                key = f"face_{item['original_filename']}"
                is_registered_user = False
            
            if key:
                if key not in final_results_map or item['similarity'] > final_results_map[key]['similarity']:
                    # Make sure we explicitly set the is_registered flag
                    item['is_registered'] = is_registered_user
                    final_results_map[key] = item
        
        final_results_list = sorted(list(final_results_map.values()), key=lambda x: x['similarity'], reverse=True)

        # Limit to top 50 overall results
        top_n_results = final_results_list[:50]
        
        # Thorough debugging to understand which results are registered users and why
        for i, result in enumerate(top_n_results):
            # Get all the fields that might indicate this is a registered user
            is_registered_flag = result.get('is_registered', False)
            registered_user_id = result.get('registered_user_id')
            claimed_by_user_id = result.get('claimed_by_user_id')
            is_claimed = result.get('is_claimed', False)
            is_historical = result.get('is_historical', False)
            
            # Log the detailed state of each result for debugging
            current_app.logger.debug(
                f"Result {i+1}: {result.get('username')} - "
                f"is_registered={is_registered_flag}, "
                f"registered_user_id={registered_user_id}, "
                f"claimed_by_user_id={claimed_by_user_id}, "
                f"is_claimed={is_claimed}, "
                f"is_historical={is_historical}"
            )
            
            # Check all conditions that would make this a registered user
            is_actually_registered = False
            reason = []
            
            # Explicitly check if coming from users_table (most reliable indicator)
            data_source = result.get('data_source', '')
            if data_source == 'users_table':
                is_actually_registered = True
                reason.append(f"data_source is 'users_table'")
            
            if registered_user_id:
                is_actually_registered = True
                reason.append(f"has registered_user_id={registered_user_id}")
                
            if claimed_by_user_id:
                is_actually_registered = True
                reason.append(f"has claimed_by_user_id={claimed_by_user_id}")
                
            if is_claimed:
                is_actually_registered = True
                reason.append("is_claimed=True")
                
            # Look for filenames that match the pattern of registered user profile images
            filename = result.get('original_filename', '')
            if filename and filename.startswith('userprofile_'):
                is_actually_registered = True
                reason.append(f"filename '{filename}' indicates a user profile")
            
            # Update the is_registered flag if needed
            if is_actually_registered and not is_registered_flag:
                result['is_registered'] = True
                current_app.logger.debug(f"Fixed: Marked result {i+1} as registered because: {', '.join(reason)}")
            elif is_registered_flag and not is_actually_registered:
                # This is unlikely but we'll log it for completeness
                current_app.logger.debug(f"Note: Result {i+1} is marked registered but doesn't meet standard criteria")
            elif is_actually_registered:
                current_app.logger.debug(f"Confirmed: Result {i+1} is correctly marked as registered")
            else:
                current_app.logger.debug(f"Confirmed: Result {i+1} is correctly marked as unregistered")
        
        # Log the final results
        for i, result in enumerate(top_n_results):
            # Convert to string representation for certain fields to ensure they're properly serialized
            if 'is_registered' in result:
                # Ensure is_registered is explicitly a boolean for JSON serialization
                result['is_registered'] = bool(result['is_registered'])
                
            # Log in more detail including data_source
            current_app.logger.debug(
                f"Final result {i}: is_registered={result.get('is_registered')}, "
                f"username={result.get('username')}, "
                f"data_source={result.get('data_source')}, "
                f"registered_user_id={result.get('registered_user_id')}, "
                f"claimed_by_user_id={result.get('claimed_by_user_id')}"
            )
            
        return jsonify({
            "results": top_n_results,
            "total": len(top_n_results), # This will now be at most 50
            "actual_total_found_before_limit": len(final_results_list), # Optional: inform client how many were found in total
            "success": True
        })

    except Exception as e:
        current_app.logger.error(f"[SEARCH] General error in api_search: {str(e)}", exc_info=True)
        return jsonify({
            "error": "Internal server error",
            "message": "An unexpected error occurred during the search.", # Generic message for client
            "results": [], "total": 0, "success": False
        }), 500


@search_bp.route("/results")
@login_required
def search_results():
    user_image_url = None
    error_message = None
    results = []

    if not hasattr(current_user, "profile_image") or not current_user.profile_image:
        error_message = (
            "You need to have a profile image set to perform a visual search."
        )
        current_app.logger.info(
            "[SEARCH_RESULTS] User attempted visual search without a profile image."
        )
    else:
        user_image_url = normalize_profile_image_path(current_user.profile_image)
        profile_image_fs_path = resolve_profile_image_path(current_user)

        liked_face_ids = UserMatch.get_liked_face_ids_by_user(current_user.id)

        if profile_image_fs_path:
            enriched_matches, search_error = get_enriched_faiss_matches(
                user_profile_image_fs_path=profile_image_fs_path,
                faiss_index_manager=faiss_index_manager,
                current_user_id=current_user.id,
                liked_face_ids_for_current_user=liked_face_ids,
                top_k=50,  # Or adjust as needed for this route
            )
            if search_error:
                error_message = search_error
            else:
                results = enriched_matches
        else:
            error_message = "Could not resolve your profile image path. Please ensure it's set correctly."
            current_app.logger.warning(
                f"[SEARCH_RESULTS] Could not resolve profile image path for user {current_user.id}"
            )

    if not results and not error_message:
        error_message = "No visually similar faces found with valid details."

    # This route is often called via JS/AJAX expecting JSON or a partial HTML for results
    # For simplicity in this refactor, let's assume it re-renders the main search template with results.
    # If it's an AJAX endpoint, the response might need to be jsonify(results=results, error=error_message)
    # or render_template_string for a partial.
    # For now, mirroring the search_page POST return structure.

    # Get filter options for the search form, as they are needed by the template
    states = Face.get_states_list()
    decades = Face.get_decades_list()
    query = request.args.get("query", "")  # Retain any query params
    search_type = request.args.get("type", "faces")

    return render_template(
        "search.html",  # Or a specific results partial if that was the original design
        results=results,
        show_results=True,
        user_image_url=user_image_url,
        error_message=error_message,
        states=states,
        decades=decades,
        query=query,
        search_type=search_type,
    )


def search_faces(query, args):
    """Search for faces based on various criteria."""
    if query:
        # Perform text search on the `Face` model
        faces = perform_text_search(
            Face, ["filename", "school_name", "yearbook_info"], query, limit=50
        )
        return faces

    # Advanced filtering
    state = args.get("state")
    decade = args.get("decade")
    filters = []
    if state:
        filters.append(Face.state == state)
    if decade:
        filters.append(Face.decade == decade)

    return db.session.query(Face).filter(*filters).limit(50).all()


def search_users(query, args):
    """Search for users based on username or profile information."""
    if query:
        # Perform text search on the `User` model
        users = perform_text_search(
            User,
            [
                "username",
                "first_name",
                "last_name",
                "bio",
                "hometown",
                "current_location",
            ],
            query,
            limit=20,
        )

        # Apply privacy filters
        current_user_id = session.get("user_id")
        return apply_privacy_filters(users, current_user_id)

    return []


def search_claimed_profiles(query, args):
    """Search for claimed profiles matching criteria."""
    conn = get_db_connection(app=None)
    if not conn:
        return []

    try:
        cursor = conn.cursor()

        # Use LIKE for partial text matching
        search_query = f"%{query}%"

        cursor.execute(
            """
            SELECT cp.*, u.username as username
            FROM claimed_profiles cp
            JOIN users u ON cp.user_id = u.id
            WHERE cp.relationship LIKE ?
            OR cp.caption LIKE ?
            OR u.username LIKE ?
            ORDER BY cp.claimed_at DESC
            LIMIT 30
        """,
            (search_query, search_query, search_query),
        )

        claimed_profiles = []
        for profile_data in cursor.fetchall():
            claimed_profiles.append(dict(profile_data))

        # Add face details to each claimed profile
        for profile in claimed_profiles:
            face = Face.get_by_filename(profile["face_filename"])
            if face:
                profile["face"] = {
                    "yearbook_year": face.yearbook_year,
                    "school_name": face.school_name,
                    "page_number": face.page_number,
                }

        return claimed_profiles

    except Exception as e:
        current_app.logger.error(f"Error searching claimed profiles: {e}")
        return []
    finally:
        conn.close()


@search_bp.route("/discover")
@login_required
def discover():
    """Discover interesting faces and users."""
    # Featured section types
    featured_sections = [
        {
            "title": "Popular Historical Figures",
            "description": "Historical faces that many users have claimed or added to their profiles",
            "faces": get_popular_faces(10),
        },
        {
            "title": "Recently Claimed Profiles",
            "description": "Faces that users have claimed as their doppelgängers",
            "profiles": get_recent_claimed_profiles(8),
        },
        {
            "title": "Interesting Decades",
            "description": "Explore matches from specific time periods",
            "decades": Face.get_decades_list(),
        },
        {
            "title": "Faces of the Day",
            "description": "A selection of interesting historical faces",
            "faces": get_diverse_faces(15),
        },
    ]

    response = make_response(
        render_template("discover.html", sections=featured_sections)
    )

    # Add cache-busting headers
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    # Add a random query parameter to prevent browser caching
    response.headers["X-Cache-Buster"] = str(random.randint(1, 1000000)) + str(
        time.time()
    )

    return response


def get_popular_faces(limit=10):
    """Get the most popular faces based on user matches."""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()

        # Find faces with the most matches
        cursor.execute(
            """
            SELECT f.*, COUNT(um.id) as match_count 
            FROM faces f
            JOIN user_matches um ON f.filename = um.match_filename
            GROUP BY f.filename
            ORDER BY match_count DESC
            LIMIT ?
        """,
            (limit,),
        )

        faces = []
        for row in cursor.fetchall():
            face_data = dict(row)
            match_count = face_data.pop("match_count")

            face = Face(**face_data)
            face_dict = face.to_dict(include_private=True)
            face_dict["match_count"] = match_count

            # Ensure state and decade info is present
            metadata = get_metadata_for_face(face)
            face_dict["decade"] = metadata["decade"]
            face_dict["state"] = metadata["state"]

            faces.append(face_dict)

        return faces

    except Exception as e:
        current_app.logger.error(f"Error getting popular faces: {e}")
        return []
    finally:
        conn.close()


def get_recent_claimed_profiles(limit=8):
    """Get recently claimed profiles."""
    claimed_profiles = ClaimedProfile.get_recent(limit)

    profiles_with_details = []
    for profile in claimed_profiles:
        user = User.get_by_id(profile.user_id)
        face = Face.get_by_filename(profile.face_filename)

        if user and face:
            profiles_with_details.append(
                {
                    "id": profile.id,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "profile_image": user.profile_image,
                    },
                    "face": {
                        "filename": face.filename,
                        "yearbook_year": face.yearbook_year,
                        "school_name": face.school_name,
                    },
                    "relationship": profile.relationship,
                    "caption": profile.caption,
                    "claimed_at": profile.claimed_at,
                }
            )

    return profiles_with_details


def get_diverse_faces(limit=15):
    """Get a diverse selection of faces from different decades and locations."""
    # Get lists of available decades and states
    decades = Face.get_decades_list()
    states = Face.get_states_list()

    faces = []
    faces_per_group = max(1, limit // (len(decades) + len(states)))

    # Get faces from each decade
    for decade in decades[:3]:  # Limit to 3 decades for diversity
        decade_faces = Face.search({"decade": decade}, limit=faces_per_group)
        faces.extend(decade_faces)

    # Get faces from different states
    for state in states[:3]:  # Limit to 3 states for diversity
        state_faces = Face.search({"school_state": state}, limit=faces_per_group)
        faces.extend(state_faces)

    # If we didn't get enough faces, add some random ones
    if len(faces) < limit:
        remaining = limit - len(faces)
        random_faces = Face.get_random_selection(remaining)
        faces.extend(random_faces)

    # Convert faces to dicts with metadata and ensure state/decade info
    face_dicts = []
    for face in faces[:limit]:
        face_dict = face.to_dict(include_private=True)
        # Enhance with metadata
        metadata = get_metadata_for_face(face)
        face_dict["decade"] = metadata["decade"]
        face_dict["state"] = metadata["state"]
        face_dicts.append(face_dict)

    # Ensure we don't exceed the limit
    return face_dicts[:limit]


@search_bp.route("/search", methods=["GET", "POST"])
@login_required
def search_page_direct():
    """Direct access route for /search for the React frontend."""
    current_app.logger.debug(f"[DEBUG] search_page_direct called for /search, method = {request.method}")
    # Return a simple JSON response that the React app can handle
    return jsonify({
        "status": "success",
        "message": "Search page endpoint",
        "results": []
    })

@search_bp.route("/api/search/autocomplete", methods=["GET"])
def autocomplete():
    """API endpoint for search autocomplete suggestions."""
    query = request.args.get("q", "")
    search_type = request.args.get("type", "faces")

    if not query or len(query) < 2:
        return jsonify([])

    suggestions = []

    if search_type in ["faces", "all"]:
        # Add face suggestions (schools, years)
        face_suggestions = get_face_autocomplete_suggestions(query)
        suggestions.extend(face_suggestions)

    if search_type in ["users", "all"]:
        # Add user suggestions
        user_suggestions = get_user_autocomplete_suggestions(query)
        suggestions.extend(user_suggestions)

    # Return unique suggestions, prioritize exact matches
    unique_suggestions = []
    seen = set()

    for suggestion in suggestions:
        if suggestion["text"].lower() not in seen:
            seen.add(suggestion["text"].lower())
            unique_suggestions.append(suggestion)

    return jsonify(unique_suggestions[:10])  # Limit to 10 suggestions


def get_face_autocomplete_suggestions(query):
    """Get autocomplete suggestions for faces."""
    conn = get_db_connection()
    if not conn:
        return []

    suggestions = []
    try:
        cursor = conn.cursor()

        # Search for school names
        cursor.execute(
            """
            SELECT DISTINCT school_name FROM faces
            WHERE school_name LIKE ?
            LIMIT 5
        """,
            (f"%{query}%",),
        )

        for row in cursor.fetchall():
            if row["school_name"]:
                suggestions.append({"text": row["school_name"], "type": "school"})

        # Search for years
        cursor.execute(
            """
            SELECT DISTINCT yearbook_year FROM faces
            WHERE yearbook_year LIKE ?
            LIMIT 5
        """,
            (f"%{query}%",),
        )

        for row in cursor.fetchall():
            if row["yearbook_year"]:
                suggestions.append({"text": row["yearbook_year"], "type": "year"})

        return suggestions
    except Exception as e:
        current_app.logger.error(f"Error in face autocomplete: {e}")
        return []
    finally:
        conn.close()


def get_user_autocomplete_suggestions(query):
    """Get autocomplete suggestions for users."""
    conn = get_db_connection(app=None)
    if not conn:
        return []

    suggestions = []
    try:
        cursor = conn.cursor()

        # Search for usernames
        cursor.execute(
            """
            SELECT username FROM users
            WHERE username LIKE ?
            AND profile_visibility = 'public'
            LIMIT 5
        """,
            (f"%{query}%",),
        )

        for row in cursor.fetchall():
            suggestions.append({"text": row["username"], "type": "user"})

        return suggestions
    except Exception as e:
        current_app.logger.error(f"Error in user autocomplete: {e}")
        return []
    finally:
        conn.close()


@search_bp.route("/api/face/<int:face_id>/like", methods=["POST"])
@login_required
def like_face(face_id):
    """Like or unlike a face/match from search results."""
    user_id = session.get("user_id") or getattr(current_user, "id", None)
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    # Toggle like: if already liked, unlike; else, like
    liked = UserMatch.toggle_like(user_id, face_id)
    like_count = UserMatch.count_likes(face_id)

    # Notify match owner if not liking own match
    match = UserMatch.get_by_user_and_face_id(user_id=None, face_id=face_id)
    if match and match.user_id != user_id:
        from models.notification import Notification
        Notification.create(
            user_id=match.user_id,
            type=Notification.TYPE_LIKE if hasattr(Notification, 'TYPE_LIKE') else 'like',
            content="Your match card was liked from search!",
            entity_id=match.id,
            entity_type="match",
            sender_id=user_id
        )
    return jsonify({"success": True, "liked": liked, "like_count": like_count})

# === Search Calibration Route ===
@search_bp.route('/calibrate-search', methods=['POST'])
@login_required
# Assuming limiter is accessible within the blueprint context or passed/imported
# If limiter is a global app instance, you might need to access it via current_app
# @limiter.exempt # This decorator needs the limiter object, handle carefully
def calibrate_search():
    """Perform background search and save results to user profile."""
    # Redirect to the SSE endpoint
    return redirect(url_for('search.generate_calibration_progress'))

# === Search Calibration SSE Endpoint ===
@search_bp.route('/calibrate-search/progress')
@login_required
def generate_calibration_progress():
    """Generates server-sent events (SSE) for search calibration progress."""
    # The actual generation logic is moved to a helper function below
    return Response(_generate_calibration_progress(), content_type='text/event-stream')

# === Search Calibration Helper Function ===
# Moving the inner generate_progress function here as a standalone helper
def _generate_calibration_progress():
    """Helper function to generate calibration progress data for SSE."""
    try:
        # Ensure current_user is accessible and has profile_image
        from flask_login import current_user
        if not current_user or not hasattr(current_user, 'profile_image') or not current_user.profile_image or current_user.profile_image == current_app.config.get('DEFAULT_PROFILE_IMAGE', ''):
            yield f'data: {{"success": true, "progress": 100}}\n\n'
            return

        # Use current_app for accessing app configuration and root_path
        profile_pic_path = os.path.join(current_app.root_path, current_user.profile_image.lstrip('/'))

        # Ensure extract_face_encoding is imported
        from utils.face.recognition import extract_face_encoding
        encoding = extract_face_encoding(profile_pic_path)

        if encoding is not None:
            for progress in range(0, 101, 20):
                import time
                time.sleep(1)
                yield f'data: {{"success": true, "progress": {progress}}}\n\n'

            # Ensure find_similar_faces_faiss is imported
            from utils.face.recognition import find_similar_faces_faiss
            results = find_similar_faces_faiss(encoding)

            conn = None
            try:
                # Ensure get_db_connection is imported
                from utils.db.database import get_db_connection
                conn = get_db_connection()
                if conn: # Check if connection is successful
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM user_matches WHERE user_id = ?', (current_user.id,))

                    for result in results:
                        cursor.execute(
                            'INSERT INTO user_matches (user_id, match_filename, similarity_score, distance) VALUES (?, ?, ?, ?)',
                            (current_user.id, result['filename'], result.get('similarity', 0), result.get('distance', 0))
                        )

                    conn.commit()
            finally:
                if conn is not None:
                    conn.close()

            yield f'data: {{"success": true, "progress": 100}}\n\n'
            return

        yield f'data: {{"success": true, "progress": 100}}\n\n'

    except Exception as e:
        # Log the full traceback for better debugging
        import traceback
        current_app.logger.error(f"Error in _generate_calibration_progress: {e}\n{traceback.format_exc()}")
        yield f'data: {{"success": false, "error": "An error occurred during calibration.", "progress": 0}}\n\n'

# Need imports for os, time, traceback, flask, flask_login, utils.db.database, utils.face.recognition
# Most should be available in routes/search.py already

@search_bp.route('/api/search', methods=['GET'])
@login_required
def search():
    try:
        # Get current user's data for comparison
        user_data = {
            'decade': current_user.decade,
            'state': current_user.state,
            'interests': current_user.interests if hasattr(current_user, 'interests') else []
        }

        # Get historical matches
        historical_matches = HistoricalMatch.query.all()
        
        # Get registered users (excluding current user)
        registered_users = User.query.filter(User.id != current_user.id).all()

        # Combine and format results
        results = []
        
        # Add historical matches
        for match in historical_matches:
            results.append({
                'id': f'hist_{match.id}',
                'username': match.name,
                'image': match.image_url if hasattr(match, 'image_url') else None,
                'decade': match.decade,
                'state': match.state,
                'similarity': calculate_similarity(user_data, {
                    'decade': match.decade,
                    'state': match.state,
                    'interests': match.interests if hasattr(match, 'interests') else []
                }),
                'is_registered': False
            })

        # Add registered users
        for user in registered_users:
            results.append({
                'id': f'user_{user.id}',
                'username': user.username,
                'image': user.profile_image if hasattr(user, 'profile_image') else None,
                'decade': user.decade,
                'state': user.state,
                'similarity': calculate_similarity(user_data, {
                    'decade': user.decade,
                    'state': user.state,
                    'interests': user.interests if hasattr(user, 'interests') else []
                }),
                'is_registered': True
            })

        # Sort by similarity score
        results.sort(key=lambda x: x['similarity'], reverse=True)

        return jsonify({'results': results})

    except Exception as e:
        current_app.logger.error(f"Error in search: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def calculate_similarity(user1, user2):
    """Calculate similarity score between two users"""
    score = 0
    total_weight = 0
    
    # Decade match (weight: 3)
    if user1['decade'] and user2['decade'] and user1['decade'] == user2['decade']:
        score += 3
    total_weight += 3
    
    # State match (weight: 2)
    if user1['state'] and user2['state'] and user1['state'].lower() == user2['state'].lower():
        score += 2
    total_weight += 2
    
    # Interests overlap (weight: 1 per matching interest)
    common_interests = set(user1.get('interests', [])) & set(user2.get('interests', []))
    score += len(common_interests)
    total_weight += max(len(user1.get('interests', [])), len(user2.get('interests', [])))
    
    # Calculate percentage (0-100)
    return round((score / total_weight * 100) if total_weight > 0 else 0, 1)
