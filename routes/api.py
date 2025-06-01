"""
API Blueprint
=============

Provides REST API endpoints for the frontend and mobile apps.
"""

import os
import logging
import time

# Force Flask and Werkzeug to log all debug/info messages to the console
logging.basicConfig(level=logging.DEBUG, force=True)
logging.getLogger('werkzeug').setLevel(logging.DEBUG)
logging.getLogger('flask').setLevel(logging.DEBUG)
# This will guarantee that all debug/info logs show up in your console.
from flask import Blueprint, current_app, jsonify, request, session
from PIL import Image, ImageDraw, ImageFont
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required

from models.face import Face
from models.follow import Follow
from models.user_match import UserMatch
from utils.image_paths import normalize_profile_image_path
from utils.search_helpers import get_enriched_faiss_matches, resolve_profile_image_path
from utils.index.faiss_manager import faiss_index_manager
from utils.serializers import serialize_match_card

api = Blueprint("api", __name__)


# /users/current endpoint is already defined elsewhere in the application

@api.route("/profile/data")
def api_profile_data():
    logging.info('[api_profile_data] Incoming request: %s', request)

    """Get profile data for the current user from faces.db"""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "message": "Not logged in"})

    # Connect to faces.db to get user data
    from utils.db.database import get_users_db_connection

    conn = get_users_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"})

    cursor = conn.cursor()

    try:
        # First get basic user data
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()

        if not user_data:
            return jsonify({"success": False, "message": "User not found"})

        # Convert sqlite3.Row to dict for easier access with fallbacks
        user_dict = {}
        for i, column in enumerate(cursor.description):
            user_dict[column[0]] = user_data[i]
        
        logging.info(f"[api_profile_data] User dict keys: {list(user_dict.keys())}")
        
        # Ensure we have the required fields or use fallbacks
        user_id_value = user_dict.get("id", user_id)
        username_value = user_dict.get("username", "User")
        
        response = {
            "success": True,
            "user": {
                "id": user_id_value,
                "username": username_value,
                "bio": user_dict.get("bio", ""),
                "current_city": user_dict.get("current_location_city", ""),
                "hometown": user_dict.get("hometown", ""),
                "memberSince": user_dict.get("created_at", ""),
                "email": user_dict.get("email", ""),
                "phone": user_dict.get("phone", ""),
                "full_name": user_dict.get("full_name", "")
            }
        }

        # Handle profile image URL
        if "profile_image" in user_dict and user_dict["profile_image"]:
            profile_image_url = f"/static/profile_pics/{user_dict['profile_image']}"
            response["user"]["profile_image_url"] = profile_image_url

        # Handle cover photo URL
        if "cover_photo" in user_dict and user_dict["cover_photo"]:
            cover_photo_url = user_dict["cover_photo"]
            if not cover_photo_url.startswith('/'):
                cover_photo_url = f"/{cover_photo_url}"
            response["user"]["cover_photo_url"] = cover_photo_url
            current_app.logger.info(f"Cover photo URL: {cover_photo_url}")
        else:
            # Set default cover photo URL
            default_cover_photo = "/static/images/default_cover_photo.png"
            response["user"]["cover_photo_url"] = default_cover_photo
            current_app.logger.info(f"Using default cover photo: {default_cover_photo}")

        logging.info('[api_profile_data] Outgoing response: %s', response)
        return jsonify(response)
    except Exception as e:
        current_app.logger.error(f"Error in api_profile_data: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()


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
    logging.info('[api_search] Incoming request: args=%s', dict(request.args))
    if not current_user.is_authenticated:
        logging.info('[api_search] Not authenticated')
        return jsonify({"error": "Not authenticated"}), 401

    user_id = getattr(current_user, 'id', None)
    logging.info('[api_search] user_id: %s', user_id)
    logging.info('[api_search] current_user: %s', repr(current_user))

    try:
        if not hasattr(current_user, "profile_image") or not current_user.profile_image:
            logging.info('[api_search] No profile image found for user')
            return jsonify({
                "results": [],
                "note": "No profile image available for search"
            })

        profile_image_fs_path = resolve_profile_image_path(current_user)
        logging.info('[api_search] profile_image_fs_path: %s', profile_image_fs_path)
        if not profile_image_fs_path or not os.path.exists(profile_image_fs_path):
            logging.info('[api_search] Profile image not found')
            return jsonify({
                "results": [],
                "note": "Profile image not found"
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
                "results": [],
                "note": "Search error occurred",
                "error": search_error
            })

        # Format results using the unified serializer
        frontend_results = []
        for match in enriched_matches:
            # Get the face object
            face = Face.get_by_id(match.get('id'))
            if not face:
                continue
                
            # Get user if this is a registered user's face
            user = None
            if match.get('claimed_by_user_id'):
                user = User.get_by_id(match['claimed_by_user_id'])
            
            # Use the unified serializer
            card_data = serialize_match_card(face, user, match.get('similarity'))
            frontend_results.append(card_data)

        logging.info('[api_search] Outgoing response: %s', {"results": frontend_results})
        return jsonify({"results": frontend_results})

    except Exception as e:
        logging.error('[api_search] Search error: %s', str(e), exc_info=True)
        return jsonify({
            "results": [],
            "note": "Error occurred during search",
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


@api.route("/profile/data", methods=["GET", "OPTIONS"])
def api_profile_data_endpoint():
    """Get profile data for the current user."""
    # Always set CORS headers for all responses
    def set_cors_headers(response):
        origin = request.headers.get('Origin')
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '86400'  # 24 hours
        return response
    
    # Handle OPTIONS requests for CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({"success": True})
        return set_cors_headers(response)
        
    # For GET requests, require login
    if not current_user.is_authenticated:
        error_response = jsonify({"success": False, "message": "Not logged in"})
        return set_cors_headers(error_response), 401
        
    try:
        user_id = current_user.id
        if not user_id:
            error_response = jsonify({"success": False, "message": "Not logged in"})
            origin = request.headers.get('Origin')
            if origin:
                error_response.headers['Access-Control-Allow-Origin'] = origin
            error_response.headers['Access-Control-Allow-Credentials'] = 'true'
            return error_response, 401
        conn = get_users_db_connection()
        if not conn:
            current_app.logger.error("Failed to get database connection")
            error_response = jsonify({"success": False, "message": "Database connection error"})
            return set_cors_headers(error_response), 500
            
        cursor = conn.cursor()
        
        # Get user data
        try:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            user_data = cursor.fetchone()
            if not user_data:
                current_app.logger.error(f"No user found with id {user_id}")
                error_response = jsonify({"success": False, "message": "User not found"})
                return set_cors_headers(error_response), 404
        except Exception as db_error:
            current_app.logger.error(f"Database error fetching user: {db_error}", exc_info=True)
            error_response = jsonify({"success": False, "message": f"Database error: {str(db_error)}"})
            return set_cors_headers(error_response), 500
        
        # Get claimed faces
        try:
            cursor.execute("SELECT * FROM faces WHERE claimed_by_user_id = ?", (user_id,))
            claimed_faces = cursor.fetchall()
        except Exception as faces_error:
            current_app.logger.error(f"Database error fetching claimed faces: {faces_error}", exc_info=True)
            error_response = jsonify({"success": False, "message": f"Database error: {str(faces_error)}"})
            return set_cors_headers(error_response), 500
        
        # Convert sqlite3.Row objects to dictionaries
        user_dict = {}
        for key in user_data.keys():
            user_dict[key] = user_data[key]
            
        claimed_faces_list = []
        for face in claimed_faces:
            face_dict = {}
            for key in face.keys():
                face_dict[key] = face[key]
            claimed_faces_list.append(face_dict)
            
        # Construct response with user data
        response = {
            "success": True,
            "user": {
                "id": user_dict.get("id"),
                "username": user_dict.get("username"),
                "bio": user_dict.get("bio") or "",
                "current_city": user_dict.get("current_city") or "",
                "hometown": user_dict.get("hometown") or "",
                "memberSince": user_dict.get("memberSince") or ""
            },
            "claimed_faces": claimed_faces_list
        }

        # Always try to use a claimed face as the profile image URL
        profile_image_url = None
        if claimed_faces:
            for face in claimed_faces:
                face_path = os.path.join(current_app.root_path, "static", "faces", face["filename"])
                if os.path.isfile(face_path):
                    profile_image_url = f"/static/faces/{face['filename']}"
                    break

        # Fallback: use normalize_profile_image_path for user profile_image
        if not profile_image_url and "profile_image" in user_data and user_data["profile_image"]:
            # Normalize image path
            from utils.image_paths import normalize_profile_image_path
            profile_image_url = normalize_profile_image_path(user_data["profile_image"])

        response["user"]["profile_image_url"] = profile_image_url
        
        # Add cover photo URL if available
        if "cover_photo" in user_data and user_data["cover_photo"]:
            from utils.image_paths import normalize_profile_image_path
            cover_photo_url = normalize_profile_image_path(user_data["cover_photo"])
            response["user"]["cover_photo_url"] = cover_photo_url
            response["user"]["cover_photo"] = user_data["cover_photo"]  # Keep the original path too

        # Return the response with CORS headers
        response_obj = jsonify(response)
        return set_cors_headers(response_obj)
    except Exception as e:
        current_app.logger.error(f"Error in api_profile_data: {str(e)}", exc_info=True)
        error_response = jsonify({"success": False, "message": f"Error: {str(e)}"})
        return set_cors_headers(error_response), 500

@api.route("/social/feed/create_post", methods=["POST", "OPTIONS"])
def api_feed_create_post():
    """Proxy endpoint for creating a post in the feed."""
    # Handle OPTIONS requests for CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({"success": True})
        origin = request.headers.get('Origin')
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '86400'  # 24 hours
        return response
    
    # For POST requests, require login
    if not current_user.is_authenticated:
        error_response = jsonify({"success": False, "message": "Not logged in"})
        origin = request.headers.get('Origin')
        if origin:
            error_response.headers['Access-Control-Allow-Origin'] = origin
        error_response.headers['Access-Control-Allow-Credentials'] = 'true'
        return error_response, 401
    
    try:
        from models.social import Post
        user_id = current_user.id
        
        # Extract data from request
        content = None
        face_filename = None
        
        if request.is_json:
            try:
                data = request.get_json()
                content = data.get("content")
                face_filename = data.get("face_filename")
                image_url = data.get("image_url")
                match_data = data.get("matchData")
                
                # Try to get face_filename from multiple sources
                if not face_filename:
                    # First try to get it from matchData if available
                    if match_data and isinstance(match_data, dict) and 'filename' in match_data:
                        face_filename = match_data['filename']
                    # Then try to extract from image_url if available
                    elif image_url:
                        if "/static/faces/" in image_url:
                            face_filename = image_url.split("/static/faces/")[-1]
                        elif "/static/extracted_faces/" in image_url:
                            face_filename = image_url.split("/static/extracted_faces/")[-1]
                        else:
                            face_filename = image_url.split("/")[-1]  # Get the last part of the URL
            except Exception as e:
                return jsonify({"success": False, "error": f"Invalid JSON data: {str(e)}"}), 400
        else:
            content = request.form.get("content")
            face_filename = request.form.get("face_filename")

        if not content and not face_filename:
            return jsonify({
                "success": False,
                "error": "Post content or image is required"
            }), 400

        # Create the post - only use columns that exist in the database schema
        current_app.logger.debug(f"api_feed_create_post: creating post with user_id={user_id}, content={content}, face_filename={face_filename}")
        
        # Check the database schema to see if face_filename column exists
        conn = None
        try:
            from utils.db.database import get_users_db_connection
            from models.user_match import UserMatch
            
            current_app.logger.debug(f"Getting database connection...")
            conn = get_users_db_connection()
            if not conn:
                current_app.logger.error("Failed to get database connection")
                raise Exception("Database connection failed")
            
            cursor = conn.cursor()
            current_app.logger.debug(f"Checking posts table schema...")
            cursor.execute("PRAGMA table_info(posts)")
            columns = [column[1] for column in cursor.fetchall()]
            current_app.logger.debug(f"api_feed_create_post: posts table columns: {columns}")
            
            # Create a post with the content
            if not content and face_filename:
                # If we only have face_filename but no content, create a default content
                content = "Shared a match"
                current_app.logger.debug(f"Created default content: {content}")
            
            # Add information about the face match to the content if it's not already there
            if face_filename and "match" not in content.lower():
                content = f"{content} #match #{face_filename}"
                current_app.logger.debug(f"Added face_filename to content: {content}")
            
            # Create the post
            current_app.logger.debug(f"Creating post with user_id={user_id}, content={content}, is_match_post={1 if face_filename else 0}, face_filename={face_filename}")
            post = Post.create(
                user_id=user_id,
                content=content,
                is_match_post=1 if face_filename else 0,  # Set is_match_post flag if we have a face_filename
                face_filename=face_filename  # Store the face_filename directly in the post
            )
            current_app.logger.debug(f"Post created: {post}")
                
            # If we have a face_filename, create or update a UserMatch record to associate it with the post
            if face_filename and post:
                try:
                    # Check if a UserMatch already exists for this user and face
                    match = UserMatch.get_by_user_and_filename(user_id, face_filename)
                    
                    if not match:
                        # Create a new UserMatch record
                        current_app.logger.debug(f"Creating new UserMatch with user_id={user_id}, match_filename={face_filename}, post_id={post.id}")
                        match = UserMatch.create(
                            user_id=user_id,
                            match_filename=face_filename,
                            post_id=post.id  # Link to the post
                        )
                        current_app.logger.debug(f"Created new UserMatch: {match}")
                    else:
                        # Update existing UserMatch to link to this post
                        current_app.logger.debug(f"Updating existing UserMatch {match.id} with post_id={post.id}")
                        match.update_post_id(post.id)
                        current_app.logger.debug(f"Updated existing UserMatch: {match}")
                except Exception as match_error:
                    # Log the error but don't fail the post creation
                    current_app.logger.error(f"Error linking match to post: {match_error}", exc_info=True)
                    # Continue with post creation even if match linking fails
        finally:
            if conn:
                conn.close()
        current_app.logger.debug(f"api_feed_create_post: post created successfully: {post}")
        
        if post:
            response = jsonify({
                "success": True,
                "post": post.to_dict(user_id=user_id)
            })
            # Add CORS headers
            origin = request.headers.get('Origin')
            if origin:
                response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response
        else:
            error_response = jsonify({
                "success": False,
                "error": "Failed to create post"
            })
            # Add CORS headers
            origin = request.headers.get('Origin')
            if origin:
                error_response.headers['Access-Control-Allow-Origin'] = origin
            error_response.headers['Access-Control-Allow-Credentials'] = 'true'
            return error_response, 500
    except Exception as e:
        current_app.logger.error(f"Error creating post: {e}")
        # Print the full stack trace for debugging
        current_app.logger.error("Full traceback:")
        current_app.logger.error(traceback.format_exc())
        
        # Log request data for debugging
        try:
            if request.is_json:
                current_app.logger.debug(f"Request JSON data: {request.get_json()}")
            else:
                current_app.logger.debug(f"Request form data: {request.form}")
        except Exception as req_error:
            current_app.logger.error(f"Error logging request data: {req_error}")
        
        error_response = jsonify({
            "success": False,
            "error": str(e)
        })
        # Add CORS headers
        origin = request.headers.get('Origin')
        if origin:
            error_response.headers['Access-Control-Allow-Origin'] = origin
        error_response.headers['Access-Control-Allow-Credentials'] = 'true'
        return error_response, 500

@api.route("/social/feed/", methods=["GET"])
@login_required
def api_social_feed():
    """Proxy endpoint for getting the social feed."""
    try:
        from models.social import Post
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"success": False, "message": "Not logged in"}), 401

        # Get posts for the feed with retry logic
        max_retries = 3
        retry_delay = 1  # seconds
        for attempt in range(max_retries):
            try:
                posts = Post.get_feed()
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    current_app.logger.warning(f"Feed fetch attempt {attempt + 1} failed: {e}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    current_app.logger.error(f"Failed to fetch feed after {max_retries} attempts: {e}")
                    return jsonify({
                        "success": False,
                        "error": "Failed to fetch feed. Please try again later."
                    }), 500

        # Format posts for JSON response using the new match_card field
        formatted_posts = [post.to_dict(user_id=user_id) for post in posts]
        return jsonify({
            "posts": formatted_posts,
            "success": True
        })
    except Exception as e:
        current_app.logger.error(f"Error getting social feed: {e}")
        return jsonify({
            "success": False,
            "error": "An error occurred while fetching the feed. Please try again later."
        }), 500

@api.route("/social/notifications/unread_count", methods=["GET"])
@login_required
def api_notifications_unread_count():
    """Proxy endpoint for getting unread notification count."""
    try:
        from models.notification import Notification
        
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

    # Get the profile image URL - NEVER use default images for search
    profile_image_url = None
    if hasattr(current_user, "profile_image") and current_user.profile_image:
        from utils.image_paths import normalize_profile_image_path
        profile_image_url = normalize_profile_image_path(current_user.profile_image)
    
    # If no profile image in user table, check faces table for claimed faces
    if not profile_image_url:
        try:
            from models.face import Face
            # Query for faces claimed by this user
            face = Face.get_claimed_by_user(current_user.id)
            if face and face.filename:
                from utils.image_paths import normalize_extracted_face_path
                profile_image_url = normalize_extracted_face_path(face.filename)
        except Exception as e:
            current_app.logger.error(f"Error getting claimed face: {str(e)}", exc_info=True)
    
    # Only use default image as last resort for UI display, never for search functions
    if not profile_image_url:
        profile_image_url = "/static/images/default_profile.jpg"
    
    response = jsonify({
        "success": True,
        "authenticated": True,
        "user": {
            "id": current_user.id,
            "username": getattr(current_user, "username", "@user"),
            "profile_image_url": profile_image_url,
            "detail": detail or ""
        }
    })
    
    # Ensure CORS headers are set in the response
    origin = request.headers.get('Origin')
    if origin:
        response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    
    return response

@api.route('/social/feed/like_post/<int:post_id>', methods=['POST'])
@login_required
def api_feed_like_post(post_id):
    """Like or unlike a post."""
    try:
        from models.social import Post, Like
        from app import db
        
        # Get the post
        post = Post.query.get_or_404(post_id)
        
        # Check if user has already liked the post
        existing_like = Like.query.filter_by(
            user_id=current_user.id,
            post_id=post_id
        ).first()
        
        if existing_like:
            # Unlike the post
            db.session.delete(existing_like)
            user_has_liked = False
        else:
            # Like the post
            like = Like(
                user_id=current_user.id,
                post_id=post_id
            )
            db.session.add(like)
            user_has_liked = True
            
        try:
            db.session.commit()
        except Exception as db_error:
            db.session.rollback()
            current_app.logger.error(f"Database error in like_post: {str(db_error)}")
            return jsonify({
                'success': False,
                'error': 'Database error occurred'
            }), 500
        
        # Get updated likes count
        likes_count = len(post.likes) if post.likes else 0
        
        return jsonify({
            'success': True,
            'likes_count': likes_count,
            'user_has_liked': user_has_liked
        })
        
    except Exception as e:
        current_app.logger.error(f"Error liking post: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to like post'
        }), 500
