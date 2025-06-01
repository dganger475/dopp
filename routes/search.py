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
from extensions import db
from models.user import User
from models.user_match import UserMatch
from routes.auth import login_required
from utils.db.database import get_db_connection, get_users_db_connection
from utils.face.metadata import enhance_face_with_metadata, get_metadata_for_face
from utils.image_paths import normalize_profile_image_path, normalize_extracted_face_path
from utils.index.faiss_manager import faiss_index_manager
from utils.search_helpers import (
    apply_privacy_filters,
    get_enriched_faiss_matches,
    perform_text_search,
    resolve_profile_image_path,
)
from utils.face.recognition import extract_face_encoding, find_similar_faces_faiss, calculate_similarity
from models.user_match import UserMatch
from utils.serializers import serialize_match_card

search = Blueprint("search", __name__)


@search.route("/", methods=["GET"])
@login_required
def search_page():
    """Display the search page."""
    return render_template("search.html")


@search.route("/api/search", methods=["GET"])
def api_search():
    """API endpoint for finding lookalikes using face similarity search (FAISS and registered users)."""
    current_app.logger.info("[SEARCH] API search endpoint called")

    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not authenticated", "success": False}), 401

    user = User.get_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found", "success": False}), 401

    # Check if user exists in faces.db to ensure we have proper profile data
    conn_users = get_users_db_connection()
    if not conn_users:
        return jsonify({"error": "Database connection failed", "success": False}), 500

    cursor = conn_users.cursor()
    cursor.execute("SELECT id, profile_image, face_encoding FROM users WHERE id = ?", (user_id,))
    user_db_record = cursor.fetchone()
        
    if not user_db_record:
        return jsonify({
            "error": "User record not found in database",
            "message": "Could not find your user record. Please try logging in again.",
            "results": [], "total": 0, "success": False
        }), 400

    # Initialize variables for profile image path
    profile_image_fs_path = None
    has_profile_image = False
    
    try:
        # Check if user has stored face encoding in users table
        if user_db_record and user_db_record['face_encoding']:
            has_profile_image = True
        
        # Also check if user has a claimed face in the faces table
        cursor.execute("SELECT filename FROM faces WHERE claimed_by_user_id = ?", (user_id,))
        claimed_face = cursor.fetchone()
        if claimed_face:
            has_profile_image = True
            # If we have a claimed face, use it as the profile image
            if claimed_face['filename']:
                profile_image_fs_path = os.path.join(current_app.root_path, 'static', 'faces', claimed_face['filename'])
        
        # Try to resolve from user profile if not found yet
        if not has_profile_image or not profile_image_fs_path:
            profile_image_fs_path = resolve_profile_image_path(user)
            if profile_image_fs_path and os.path.exists(profile_image_fs_path):
                has_profile_image = True
        
        # Last attempt - check if there's a userprofile_[user_id] file in faces directory
        if not has_profile_image or not profile_image_fs_path:
            potential_profile_file = f"userprofile_{user_id}.jpg"
            potential_path = os.path.join(current_app.root_path, 'static', 'faces', potential_profile_file)
            
            if os.path.exists(potential_path):
                profile_image_fs_path = potential_path
                has_profile_image = True
                current_app.logger.debug(f"[SEARCH] Found user profile in faces dir: {profile_image_fs_path}")
        
        # Return available search data (no face matching) for users without profile images
        # This allows the search page to load even if the user doesn't have a face photo
        if not has_profile_image or not profile_image_fs_path or not os.path.exists(profile_image_fs_path):
            # Return basic search data without face matching
            return jsonify({
                "warning": "No profile image available for face matching",
                "message": "Upload a profile image to enable face matching",
                "results": [], 
                "total": 0, 
                "hasProfileImage": False,
                "success": True
            })

        # Load the image and detect faces
        image = face_recognition.load_image_file(profile_image_fs_path)
        face_locations = face_recognition.face_locations(image)
        if not face_locations:
            return jsonify({
                "error": "No face detected in profile image",
                "message": "Could not detect a face in your profile image. Please upload a clear face photo.",
                "results": [], "total": 0, "success": False
            }), 400
            
        # Get face encoding from the detected face
        current_user_face_encoding = face_recognition.face_encodings(image, face_locations)[0]

        # 1. Fetch FAISS matches (historical photos)
        faiss_results_formatted = []
        # Get liked faces for the current user
        liked_face_ids = UserMatch.get_liked_face_ids_by_user(user.id)
        
        try:
            # Do FAISS search with face recognition to find matches
            faiss_matches_raw, faiss_error = get_enriched_faiss_matches(
                user_profile_image_fs_path=profile_image_fs_path,
                faiss_index_manager=faiss_index_manager,
                current_user_id=user.id,
                liked_face_ids_for_current_user=liked_face_ids,
                top_k=50
            )
            if faiss_error:
                current_app.logger.error(f"[SEARCH] Error fetching FAISS matches: {faiss_error}")
            current_app.logger.info(f"[SEARCH] FAISS raw matches count: {len(faiss_matches_raw) if faiss_matches_raw else 0}")
            if faiss_matches_raw:
                for fm_raw in faiss_matches_raw:
                    # Get the Face model or dict
                    face = fm_raw
                    user = None
                    if fm_raw.get('claimed_by_user_id'):
                        user = User.get_by_id(fm_raw['claimed_by_user_id'])
                    similarity = fm_raw.get('similarity')
                    current_app.logger.debug(f"[SEARCH] FAISS match raw data: {fm_raw}")
                    current_app.logger.debug(f"[SEARCH] FAISS match similarity: {similarity}")
                    faiss_results_formatted.append(serialize_match_card(face, user=user, similarity=similarity))
            current_app.logger.info(f"[SEARCH] FAISS formatted results count: {len(faiss_results_formatted)}")
        except Exception as e_faiss:
            current_app.logger.error(f"[SEARCH] Exception during FAISS search: {str(e_faiss)}")

        # 2. Fetch Registered User Matches
        registered_user_results_formatted = []
        conn_users = None
        try:
            conn_users = get_users_db_connection()
            cursor = conn_users.cursor()
            
            # First try to get users with non-default images and valid face encodings
            cursor.execute("""
                SELECT u.id, u.username, u.profile_image, u.face_encoding, u.current_location_city, u.current_location_state
                FROM users u WHERE u.id != ? AND u.face_encoding IS NOT NULL AND u.profile_image IS NOT NULL
                AND u.profile_image NOT LIKE '%default%' AND u.profile_image != ''
            """, (user.id,))
            
            # Additionally get users who have claimed faces (they may not have profile_image set correctly)
            claimed_cursor = conn_users.cursor()
            claimed_cursor.execute("""
                SELECT u.id, u.username, f.filename as profile_image, u.face_encoding, u.current_location_city, u.current_location_state
                FROM users u
                JOIN faces f ON f.claimed_by_user_id = u.id
                WHERE u.id != ? AND u.face_encoding IS NOT NULL
            """, (user.id,))
            
            # Combine both result sets
            other_users = cursor.fetchall()
            claimed_users = claimed_cursor.fetchall()
            
            # Add claimed users to the results
            if claimed_users:
                other_users = list(other_users) + list(claimed_users)
                current_app.logger.debug(f"[SEARCH] Found {len(other_users)} total users, including {len(claimed_users)} with claimed faces")
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
                        # Normalize the profile image path to ensure we're using the correct one from faces.db
                        if other_profile_image.startswith('userprofile_'):
                            image_url = f"/static/faces/{other_profile_image}"
                        elif other_profile_image.startswith('/static/'):
                            image_url = other_profile_image
                        else:
                            # Check if the file exists in profile_pics directory
                            profile_pic_path = os.path.join(current_app.root_path, 'static', 'profile_pics', other_profile_image)
                            if os.path.exists(profile_pic_path):
                                image_url = f"/static/profile_pics/{other_profile_image}"
                            else:
                                # Try faces directory as fallback
                                faces_path = os.path.join(current_app.root_path, 'static', 'faces', other_profile_image)
                                if os.path.exists(faces_path):
                                    image_url = f"/static/faces/{other_profile_image}"
                                else:
                                    # Check specifically in faces.db before falling back to default
                                    # Check if the user has a userprofile_ image in the faces table
                                    try:
                                        face_cursor = conn_users.cursor()
                                        face_cursor.execute(
                                            "SELECT filename FROM faces WHERE claimed_by_user_id = ?",
                                            (other_user_id,)
                                        )
                                        face_record = face_cursor.fetchone()
                                        if face_record and face_record['filename']:
                                            # Use the filename from faces table
                                            image_url = f"/static/faces/{face_record['filename']}"
                                            current_app.logger.debug(f"[SEARCH] Found user image in faces table: {image_url}")
                                        else:
                                            # Last resort: normalized path from the database without defaulting
                                            image_url = normalize_profile_image_path(other_profile_image)
                                    except Exception as e:
                                        current_app.logger.error(f"[SEARCH] Error checking faces table: {e}")
                                        # Last resort: normalized path from the database
                                        image_url = normalize_profile_image_path(other_profile_image)

                        # Calculate the location string for display
                        location_display = ''
                        if other_city and other_state:
                            location_display = f"{other_city}, {other_state}"
                        elif other_state:
                            location_display = other_state
                        # Don't filter based on similarity yet - include all and sort later
                        # These are ALWAYS registered users since they come from the users table
                        registered_user_results_formatted.append({
                            "id": f"user_{other_user_id}",
                            "username": other_username,
                            "image": image_url,
                            "safe_image_path": image_url,  # Add this for consistency with FAISS results
                            "decade": "",
                            "state": other_state or "",
                            "similarity": float(similarity_score),  # Keep as 0-100 percentage
                            "is_registered": True,  # Explicitly mark as registered
                            "is_historical": False,
                            "location": f"{other_city}, {other_state}" if other_city and other_state else (other_city or other_state or ""),
                            "registered_user_id": other_user_id,
                            "data_source": "users_table"  # Track data source
                        })
                        current_app.logger.debug(f"[SEARCH] Registered user match found: {other_username} with similarity {similarity_score} and image {image_url}")
                    except Exception as e_encoding:
                        current_app.logger.error(f"[SEARCH] Error processing encoding for user {other_user_id}: {str(e_encoding)}")
                        continue
        except Exception as e_users_search:
            current_app.logger.error(f"[SEARCH] Exception during registered users search: {str(e_users_search)}")
        finally:
            if conn_users: conn_users.close()

        # 3. Combine and Deduplicate
        all_results_combined = faiss_results_formatted + registered_user_results_formatted
        current_app.logger.info(f"[SEARCH] Combined results before deduplication: {len(all_results_combined)}")
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
        
        final_results_list = list(final_results_map.values())
        current_app.logger.info(f"[SEARCH] Results after deduplication: {len(final_results_list)}")
        # Limit to top 50 overall results
        top_n_results = final_results_list[:50]
        current_app.logger.info(f"[SEARCH] Top N results to return: {len(top_n_results)}")
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
        
        # Log the final results and send notifications to registered users
        from models.notification import Notification
        
        for i, result in enumerate(top_n_results):
            # Convert to string representation for certain fields to ensure they're properly serialized
            if 'is_registered' in result:
                # Ensure is_registered is explicitly a boolean for JSON serialization
                result['is_registered'] = bool(result['is_registered'])
            
            # Send notification to registered users when they appear in search results
            try:
                # Get the user ID of the registered user in the search results
                target_user_id = None
                if result.get('is_registered'):
                    if result.get('registered_user_id'):
                        target_user_id = result.get('registered_user_id')
                    elif result.get('claimed_by_user_id'):
                        target_user_id = result.get('claimed_by_user_id')
                
                # Only send notification if this is a registered user
                if target_user_id and target_user_id != user_id:
                    # Create a notification for the user who appeared in search results
                    Notification.create(
                        user_id=target_user_id,
                        type=Notification.TYPE_SEARCH_APPEARANCE,
                        content=f"You appeared in someone's search results!",
                        entity_id=str(user_id),  # The searcher's user ID
                        entity_type="user",
                        sender_id=user_id  # The searcher's user ID
                    )
                    current_app.logger.debug(f"[SEARCH] Sent search appearance notification to user {target_user_id}")
            except Exception as e:
                current_app.logger.error(f"[SEARCH] Error sending notification: {e}")
                
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


@search.route("/results")
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

    # Return JSON for React frontend
    # Remove any default image assignment for face matching; let frontend handle missing images
    return jsonify({
        "results": results,
        "show_results": True,
        "user_image_url": user_image_url,
        "error_message": error_message,
        "states": states,
        "decades": decades,
        "query": query,
        "search_type": search_type
    })


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
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Use LIKE for partial text matching
            search_query = f"%{query}%"

            cursor.execute(
                """
                SELECT cp.*, u.username as username, f.filename as face_filename
                FROM claimed_profiles cp
                JOIN users u ON cp.user_id = u.id
                JOIN faces f ON cp.face_id = f.id
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
                profile_dict = dict(profile_data)
                # Add face details to each claimed profile
                face = Face.get_by_id(profile_dict["face_id"])
                if face:
                    profile_dict["face"] = {
                        "yearbook_year": face.yearbook_year,
                        "school_name": face.school_name,
                        "page_number": face.page_number,
                    }
                claimed_profiles.append(profile_dict)

            return claimed_profiles

    except Exception as e:
        current_app.logger.error(f"Error searching claimed profiles: {e}")
        return []


@search.route("/discover")
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
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT cp.*, u.username, f.filename as face_filename
                FROM claimed_profiles cp
                JOIN users u ON cp.user_id = u.id
                JOIN faces f ON cp.face_id = f.id
                ORDER BY cp.claimed_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            profiles = cursor.fetchall()

            profiles_with_details = []
            for profile in profiles:
                profile_dict = dict(profile)
                user = User.get_by_id(profile_dict["user_id"])
                face = Face.get_by_id(profile_dict["face_id"])

                if user and face:
                    profiles_with_details.append(
                        {
                            "id": profile_dict["id"],
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
                            "relationship": profile_dict["relationship"],
                            "caption": profile_dict["caption"],
                            "claimed_at": profile_dict["claimed_at"],
                        }
                    )

            return profiles_with_details
    except Exception as e:
        current_app.logger.error(f"Error getting recent claimed profiles: {e}")
        return []


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


@search.route("/search", methods=["GET", "POST"])
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

@search.route("/api/search/autocomplete", methods=["GET"])
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


@search.route("/api/face/<int:face_id>/like", methods=["POST"])
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
@search.route('/calibrate-search', methods=['POST'])
@login_required
# Assuming limiter is accessible within the blueprint context or passed/imported
# If limiter is a global app instance, you might need to access it via current_app
# @limiter.exempt # This decorator needs the limiter object, handle carefully
def calibrate_search():
    """Perform background search and save results to user profile."""
    # Redirect to the SSE endpoint
    return redirect(url_for('search.generate_calibration_progress'))

# === Search Calibration SSE Endpoint ===
@search.route('/calibrate-search/progress')
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

@search.route('/api/search/legacy', methods=['GET'])
@login_required
def search_legacy():
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
