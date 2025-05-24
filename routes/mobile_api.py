"""
Mobile API endpoints for the DoppleGänger app.
These endpoints are specifically designed for the mobile application.
"""

import base64
import io
import json
import os
import pickle
import time
import uuid
from datetime import datetime, timedelta
from functools import wraps

import face_recognition
import jwt
from flask import Blueprint, current_app, jsonify, request, session
from PIL import Image
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

import numpy as np

# Import models
from models.user import User
from utils.db.database import get_db_connection, get_users_db_connection
from utils.index.faiss_manager import faiss_index_manager

# from routes.face_matching_new import query_faces_directly  # Removed: file deleted, use canonical search logic

# Create blueprint
mobile_api = Blueprint("mobile_api", __name__)

# --- Disable CSRF for API endpoints ---
# If you use Flask-WTF or a custom CSRF middleware, exempt this blueprint here.
# If not, this is a no-op and safe to add.
from utils.csrf import csrf

if csrf is not None:
    csrf.exempt(mobile_api)
# If CSRF is globally disabled, csrf will be None and no action is needed.

# JWT Secret key
JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "your-jwt-secret-key-change-this")
JWT_EXPIRATION = 60 * 60 * 24 * 7  # 7 days


# Token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"message": "Token is missing", "success": False}), 401

        try:
            # Decode token
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            current_user_id = data["user_id"]

            # Get user from database
            user = User.get_by_id(current_user_id)
            if not user:
                return jsonify({"message": "User not found", "success": False}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired", "success": False}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token", "success": False}), 401

        return f(user, *args, **kwargs)

    return decorated


@mobile_api.route("/auth/login", methods=["POST"])
def login():
    """Login endpoint for mobile app."""
    print("Mobile API login endpoint called")

    data = request.json
    print(f"Request data: {data}")

    if not data or not data.get("email") or not data.get("password"):
        print("Email or password missing")
        return (
            jsonify({"message": "Email and password are required", "success": False}),
            400,
        )

    email = data.get("email")
    password = data.get("password")
    print(f"Login attempt for email: {email}")

    # Get user from database
    user = User.get_by_email(email)
    if not user:
        print(f"User not found for email: {email}")
        return jsonify({"message": "User not found", "success": False}), 401

    print(f"User found: {user.username}, ID: {user.id}")

    # Check password
    password_valid = check_password_hash(user.password_hash, password)
    print(f"Password valid: {password_valid}")

    if not password_valid:
        print("Invalid password")
        return jsonify({"message": "Invalid password", "success": False}), 401

    # Generate JWT token
    token = jwt.encode(
        {
            "user_id": user.id,
            "exp": datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION),
        },
        JWT_SECRET,
        algorithm="HS256",
    )

    # Return token and user data
    return jsonify(
        {
            "success": True,
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "profile_image": user.profile_image,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
        }
    )


@mobile_api.route("/auth/register", methods=["POST"])
def register():
    """Register endpoint for mobile app."""
    data = request.json

    if (
        not data
        or not data.get("email")
        or not data.get("password")
        or not data.get("username")
    ):
        return (
            jsonify(
                {
                    "message": "Email, username, and password are required",
                    "success": False,
                }
            ),
            400,
        )

    email = data.get("email")
    username = data.get("username")
    password = data.get("password")

    # Check if user already exists
    existing_user = User.get_by_email(email)
    if existing_user:
        return jsonify({"message": "Email already registered", "success": False}), 400

    existing_username = User.get_by_username(username)
    if existing_username:
        return jsonify({"message": "Username already taken", "success": False}), 400

    # Create new user
    new_user = User.create(
        username=username,
        email=email,
        password=password,
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
    )

    if not new_user:
        return jsonify({"message": "Error creating user", "success": False}), 500

    # Generate JWT token
    token = jwt.encode(
        {
            "user_id": new_user.id,
            "exp": datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION),
        },
        JWT_SECRET,
        algorithm="HS256",
    )

    # Return token and user data
    return jsonify(
        {
            "success": True,
            "token": token,
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "profile_image": new_user.profile_image,
                "first_name": new_user.first_name,
                "last_name": new_user.last_name,
            },
        }
    )


@mobile_api.route("/profile/", methods=["GET"])
@token_required
def get_profile(user):
    """Get user profile data."""
    # Get user matches count
    from models.social import ClaimedProfile
    from models.user_match import UserMatch

    # Get claimed profiles
    claimed_profiles = ClaimedProfile.get_by_user_id(user.id)
    claimed_count = len(claimed_profiles) if claimed_profiles else 0

    # Get matches added to profile
    user_matches = UserMatch.get_by_user_id(user.id)
    added_count = len(user_matches) if user_matches else 0

    # Total count (avoid duplicates)
    claimed_filenames = (
        [profile.face_filename for profile in claimed_profiles]
        if claimed_profiles
        else []
    )
    added_filenames = (
        [match.match_filename for match in user_matches] if user_matches else []
    )

    # Combine both sets to avoid duplicates
    all_match_filenames = set(claimed_filenames + added_filenames)
    total_matches = len(all_match_filenames)

    # Get followers and following count
    from models.follow import Follow

    followers = Follow.get_followers(user.id)
    followers_count = len(followers) if followers else 0

    following = Follow.get_following(user.id)
    following_count = len(following) if following else 0

    # Return user profile data
    return jsonify(
        {
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "profile_image": user.profile_image,
                "cover_photo": user.cover_photo,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "bio": user.bio,
                "hometown": user.hometown,
                "current_location": user.current_location,
                "birthdate": user.birthdate,
                "website": user.website,
                "interests": user.interests,
                "profile_visibility": user.profile_visibility,
                "created_at": user.created_at,
            },
            "stats": {
                "matches": total_matches,
                "followers": followers_count,
                "following": following_count,
            },
        }
    )


@mobile_api.route("/profile/", methods=["PUT", "POST"])
def update_profile():
    """Update user profile - handles both PUT and POST methods"""

    try:
        # Update user fields
        if "username" in data:
            user.username = data["username"]
        if "first_name" in data:
            user.first_name = data["first_name"]
        if "last_name" in data:
            user.last_name = data["last_name"]
        if "email" in data:
            user.email = data["email"]

        # Save changes
        user.save()

        return jsonify(
            {
                "success": True,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "profile_image": user.profile_image,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            }
        )
    except Exception as e:
        current_app.logger.error(f"Error updating profile: {e}")
        return (
            jsonify({"message": f"Error updating profile: {str(e)}", "success": False}),
            500,
        )


@mobile_api.route("/profile/upload-photo", methods=["POST"])
@token_required
def upload_profile_photo_mobile(user):
    """Upload profile photo."""
    if "image" not in request.json:
        return jsonify({"message": "No image provided", "success": False}), 400

    try:
        image_data = request.json["image"]

        # Remove data URL prefix if present
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]

        # Decode base64 image
        image_bytes = base64.b64decode(image_data)

        # Generate unique filename
        filename = f"{user.id}_{int(time.time())}.jpg"
        filepath = os.path.join(current_app.config["PROFILE_PICS"], filename)

        # Save image
        with open(filepath, "wb") as f:
            f.write(image_bytes)

        # Update user profile image
        user.profile_image = filename
        user.save()

        return jsonify(
            {
                "success": True,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "profile_image": user.profile_image,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
            }
        )
    except Exception as e:
        current_app.logger.error(f"Error uploading profile photo: {e}")
        return (
            jsonify(
                {
                    "message": f"Error uploading profile photo: {str(e)}",
                    "success": False,
                }
            ),
            500,
        )


@mobile_api.route("/faces/match", methods=["POST"])
@token_required
def match_face(user):
    """Match face from photo."""
    try:
        if "photo" not in request.files:
            return jsonify({"message": "No photo provided", "success": False}), 400

        photo = request.files["photo"]
        if not photo:
            return jsonify({"message": "Empty photo provided", "success": False}), 400

        # Save the uploaded photo temporarily
        temp_folder = os.path.join(current_app.root_path, "temp")
        os.makedirs(temp_folder, exist_ok=True)
        temp_filename = f"temp_{uuid.uuid4()}.jpg"
        temp_path = os.path.join(temp_folder, temp_filename)
        photo.save(temp_path)

        try:
            # First try to use face recognition with FAISS
            fallback_mode = False
            matches = []

            try:
                # Extract face encoding from uploaded photo
                from utils.face.recognition import (
                    extract_face_encoding,
                    find_similar_faces,
                )

                # from utils.face_context_fix import extract_with_app_context (module removed, logic should be refactored if needed)
                # Get a wrapped version of extract_face_encoding that handles app context
                extract_func = extract_with_app_context(extract_face_encoding)

                # Try to extract the face encoding
                encoding = extract_func(temp_path)

                if encoding is not None:
                    current_app.logger.info(
                        f"Successfully extracted face encoding from uploaded photo"
                    )
                    # Use FAISS to find similar faces
                    faiss_matches = find_similar_faces(
                        encoding, top_k=20
                    )  # Get top 20 matches

                    if faiss_matches and len(faiss_matches) > 0:
                        current_app.logger.info(
                            f"Found {len(faiss_matches)} similar faces using FAISS"
                        )
                        # Use the FAISS matches
                        matches = faiss_matches
                    else:
                        current_app.logger.warning(
                            "FAISS search returned no matches, falling back to database query"
                        )
                        fallback_mode = True
                else:
                    current_app.logger.warning(
                        "Could not extract face encoding from uploaded photo"
                    )
                    fallback_mode = True
            except Exception as e:
                current_app.logger.error(f"Error in facial recognition: {e}")
                fallback_mode = True

            # If facial recognition failed, use the database query as fallback
            if fallback_mode or not matches:
                current_app.logger.info("Using direct database query as fallback")
                matches = query_faces_directly(temp_path)
                fallback_mode = True  # Mark that we used the fallback method

            # Format matches for response
            formatted_matches = []
            for match in matches:
                # Get face data from database
                conn = get_db_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            SELECT f.*, COUNT(um.id) as match_count 
                            FROM faces f 
                            LEFT JOIN user_matches um ON f.filename = um.match_filename 
                            WHERE f.filename = ? 
                            GROUP BY f.filename
                        """,
                            (match["filename"],),
                        )
                        face_data = cursor.fetchone()

                        if face_data:
                            formatted_matches.append(
                                {
                                    "filename": match["filename"],
                                    "similarity": match["similarity"],
                                    "state": face_data["school_name"],
                                    "year": face_data["yearbook_year"],
                                    "page": face_data["page_number"],
                                    "match_count": face_data["match_count"],
                                    "image_url": f"/static/extracted_faces/{match['filename']}",
                                    "fallback": match.get("fallback", False),
                                }
                            )
                    finally:
                        conn.close()

            # Save successful matches to user's history
            for match in formatted_matches[:5]:  # Save top 5 matches
                from models.user_match import UserMatch

                user_match = UserMatch.add_match(
                    user_id=user.id,
                    match_filename=match["filename"],
                    is_visible=1,  # visible by default
                    privacy_level="public",
                )
                # Update similarity if possible
                if user_match and hasattr(user_match, "update"):
                    user_match.update(similarity=match["similarity"])

            response = {
                "success": True,
                "matches": formatted_matches,
                "fallback": fallback_mode,
            }
            if fallback_mode:
                response["message"] = (
                    "Face encoding failed. Showing most popular faces as fallback."
                )
            return jsonify(response)

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except Exception as e:
        current_app.logger.error(f"Error matching face: {e}")
        return (
            jsonify({"message": f"Error matching face: {str(e)}", "success": False}),
            500,
        )


@mobile_api.route("/faces/matches", methods=["GET"])
@token_required
def get_user_matches(user):
    """Get user matches."""
    from models.social import ClaimedProfile
    from models.user_match import UserMatch
    from flask import session, jsonify
    import logging

    # Log the start of the function
    logging.info(f"Getting matches for user_id: {user.id}")
    
    # Set the user_id in the session for the duration of this request
    # This is needed because UserMatch.get_by_user_id relies on session
    session['user_id'] = user.id
    logging.info(f"Session user_id set to: {session.get('user_id')}")

    try:
        # Get user matches - pass respect_privacy=False to ensure we get all matches
        user_matches = UserMatch.get_by_user_id(user.id, respect_privacy=False)
        logging.info(f"Found {len(user_matches) if user_matches else 0} user matches")
        
        # Get claimed profiles
        claimed_profiles = ClaimedProfile.get_by_user_id(user.id)
        logging.info(f"Found {len(claimed_profiles) if claimed_profiles else 0} claimed profiles")

        # Format matches for response
        formatted_matches = []
        processed_filenames = set()  # Track processed filenames to avoid duplicates

        # Add user matches
        if user_matches:
            for match in user_matches:
                if not match.match_filename:
                    continue
                    
                # Skip if we've already processed this filename
                if match.match_filename in processed_filenames:
                    continue
                    
                # Get face data from database
                conn = get_db_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT * FROM faces WHERE filename = ?",
                            (match.match_filename,),
                        )
                        face_data = cursor.fetchone()
                        
                        if face_data:
                            formatted_match = dict(face_data)
                            # Ensure consistent field names with claimed profiles
                            formatted_match["is_claimed"] = False
                            formatted_match["face_filename"] = match.match_filename  # Add face_filename for consistency
                            formatted_match["similarity"] = (
                                match.similarity if match.similarity is not None else 0
                            )
                            formatted_match["similarity_percent"] = round(formatted_match["similarity"] * 100, 1)  # Add percentage
                            formatted_match["match_id"] = match.id
                            formatted_match["is_visible"] = bool(match.is_visible)
                            formatted_match["privacy_level"] = match.privacy_level
                            formatted_match["added_at"] = match.added_at
                            formatted_match["relationship"] = "Match"  # Default relationship for unclaimed matches
                            
                            # Add to processed filenames
                            processed_filenames.add(match.match_filename)
                            
                            # Add to results
                            formatted_matches.append(formatted_match)
                    except Exception as e:
                        logging.error(f"Error getting face data: {e}")
                    finally:
                        conn.close()

        # Add claimed profiles
        if claimed_profiles:
            for profile in claimed_profiles:
                if not profile.face_filename:
                    continue
                    
                # Skip if we've already processed this filename
                if profile.face_filename in processed_filenames:
                    continue
                    
                # Get the face data and the associated user match to get the actual similarity score
                face_data = profile.get_face_data()
                if face_data:
                    # Get the user match to find the actual similarity score
                    user_match = None
                    conn = get_db_connection()
                    if conn:
                        try:
                            cursor = conn.cursor()
                            cursor.execute(
                                """
                                SELECT um.similarity 
                                FROM user_matches um 
                                WHERE um.match_filename = ? AND um.user_id = ?
                                """,
                                (profile.face_filename, user.id)
                            )
                            match_data = cursor.fetchone()
                            if match_data:
                                user_match = dict(match_data)
                        except Exception as e:
                            logging.error(f"Error getting user match for claimed profile: {e}")
                        finally:
                            conn.close()
                    
                    # Set the claimed profile data
                    face_data["is_claimed"] = True
                    # Use the actual similarity score if available, otherwise use None
                    face_data["similarity"] = user_match.get("similarity") if user_match else None
                    face_data["match_id"] = f"claimed_{profile.id}"
                    face_data["is_visible"] = True
                    face_data["privacy_level"] = "public"
                    face_data["added_at"] = profile.claimed_at
                    
                    # Add to processed filenames
                    processed_filenames.add(profile.face_filename)
                    
                    # Add to results
                    formatted_matches.append(face_data)

        # Sort matches by added_at in descending order (newest first)
        formatted_matches.sort(key=lambda x: x.get("added_at", ""), reverse=True)
        
        logging.info(f"Returning {len(formatted_matches)} total matches")
        return jsonify({"success": True, "matches": formatted_matches})

    except Exception as e:
        logging.error(f"Error getting user matches: {e}", exc_info=True)
        return jsonify({"success": False, "message": str(e)})
    finally:
        # Clean up session if needed
        if 'user_id' in session:
            session.pop('user_id', None)
            logging.info("Cleaned up session user_id")


# Ping endpoint for mobile app connectivity check
@mobile_api.route("/ping", methods=["GET"])
def ping():
    """Simple endpoint to check if the API is reachable."""
    return jsonify(
        {
            "success": True,
            "message": "DoppleGänger API is running",
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


# Add more endpoints as needed for the mobile app
