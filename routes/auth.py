"""
Authentication Blueprint
=======================

Handles all user authentication routes with improved security and validation.
"""

import logging
import os
import sys
from pathlib import Path
from werkzeug.utils import secure_filename
from PIL import Image
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Add project root to path
PROJECT_ROOT = str(Path(__file__).parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
    jsonify,
    make_response
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)
from werkzeug.utils import secure_filename
from flask_wtf.csrf import generate_csrf
from flask_cors import cross_origin

from models.user import User
from extensions import db, limiter
from forms.auth_forms import LoginForm, RegisterForm
from utils.csrf import csrf
from utils.face.indexing import index_profile_face
from utils.exceptions import (
    AuthenticationError, ValidationError, FileUploadError
)
from middleware.security import (
    rate_limit, sanitize_input, validate_content_type
)
from utils.cache_utils import (
    get_cache_value,
    set_cache_value,
    delete_cache_value,
    increment_cache_value
)
from .config import get_profile_image_path, get_default_profile_image_path

auth = Blueprint("auth", __name__)

def save_profile_photo(file, user_id):
    """
    Save a profile photo for a user.
    
    Args:
        file: The uploaded file
        user_id: The ID of the user
        
    Returns:
        str: The filename of the saved photo
        
    Raises:
        FileUploadError: If there's an error saving the file
    """
    try:
        # Get the upload directory from config
        upload_dir = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], 'profile_photos')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate a unique filename
        ext = os.path.splitext(file.filename)[1].lower()
        filename = f"{user_id}_{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(upload_dir, filename)
        
        # Save the file
        file.save(filepath)
        
        # Validate and optimize the image
        try:
            with Image.open(filepath) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if too large
                max_size = (800, 800)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save optimized image
                img.save(filepath, 'JPEG', quality=85, optimize=True)
        except Exception as e:
            logger.warning(f"Image optimization failed: {str(e)}")
            # Continue even if optimization fails
        
        return filename
    except Exception as e:
        logger.error(f"Error saving profile photo: {str(e)}")
        raise FileUploadError("Failed to save profile photo")

def validate_password_strength(password):
    # Default values if config is missing
    min_length = current_app.config.get('PASSWORD_MIN_LENGTH', 8)
    require_uppercase = current_app.config.get('PASSWORD_REQUIRE_UPPERCASE', True)
    require_lowercase = current_app.config.get('PASSWORD_REQUIRE_LOWERCASE', True)
    require_numbers = current_app.config.get('PASSWORD_REQUIRE_NUMBERS', True)
    require_special = current_app.config.get('PASSWORD_REQUIRE_SPECIAL', True)

    if len(password) < min_length:
        raise ValidationError(f'Password must be at least {min_length} characters long')
    if require_uppercase and not any(c.isupper() for c in password):
        raise ValidationError('Password must contain at least one uppercase letter')
    if require_lowercase and not any(c.islower() for c in password):
        raise ValidationError('Password must contain at least one lowercase letter')
    if require_numbers and not any(c.isdigit() for c in password):
        raise ValidationError('Password must contain at least one number')
    if require_special and not any(not c.isalnum() for c in password):
        raise ValidationError('Password must contain at least one special character')

# =============================
# LOGIN ROUTE
# =============================
@auth.route("/login", methods=["GET", "POST", "OPTIONS"])
@rate_limit
@csrf.exempt
def login():
    if request.method == "OPTIONS":
        response = jsonify({"status": "preflight"})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    try:
        # Check if user is already logged in
        user_id = session.get('user_id')
        if user_id:
            user = User.query.get(user_id)
            if user:
                if request.is_json:
                    return jsonify({"status": "already_logged_in", "redirect": url_for("social.feed.feed_page")})
                return redirect(url_for("social.feed.feed_page"))

        if request.method == "POST":
            if request.is_json:
                data = request.get_json()
                username_or_email = sanitize_input(data.get("username") or data.get("email"))
                password = data.get("password")
            else:
                form = LoginForm()
                if form.validate_on_submit():
                    username_or_email = sanitize_input(form.email.data)
                    password = form.password.data
                else:
                    return render_template("auth/login.html", title="Login", form=form)

            if not username_or_email or not password:
                raise ValidationError("Username/Email and password are required")

            # Use SQLAlchemy session for database operations
            with db.session.begin():
                user = User.query.filter_by(username=username_or_email).first()
                if not user:
                    user = User.query.filter_by(email=username_or_email).first()
                    logger.info(f"User not found by username, trying email lookup for: {username_or_email}")

                if not user or not user.verify_password(password):
                    key = f'login_attempts:{request.remote_addr}'
                    attempts = increment_cache_value(key, timeout=3600)
                    if attempts >= 5:
                        raise AuthenticationError("Too many failed attempts. Please try again later.")
                    if request.is_json:
                        return jsonify({"error": "Invalid username or password"}), 401
                    flash("Invalid email or password", "error")
                    return render_template("auth/login.html", title="Login", form=LoginForm()), 401

                delete_cache_value(f'login_attempts:{request.remote_addr}')

                # Clear any existing session data
                session.clear()
                
                # Set up new session
                login_user(user)
                session["user_id"] = user.id
                session.permanent = True
                
                # Log successful login
                logger.info(f"User {user.username} logged in successfully", extra={'user_id': user.id})

                if request.is_json:
                    return jsonify({
                        "status": "success",
                        "access_token": user.generate_auth_token(),
                        "user": {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                            "profile_image_url": user.get_profile_image_url()
                        }
                    })
                return redirect(url_for("social.feed.feed_page"))

        return render_template("auth/login.html", title="Login", form=LoginForm())
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        if request.is_json:
            return jsonify({"error": str(e)}), 500
        flash(str(e), "error")
        return render_template("auth/login.html", title="Login", form=LoginForm())

# =============================
# CURRENT USER CHECK
# =============================
@limiter.exempt
@auth.route("/current_user", methods=["GET", "OPTIONS"])
def current_user_info():
    """
    Check if user is authenticated and return user info.
    """
    origin = request.headers.get('Origin')
    if request.method == "OPTIONS":
        response = jsonify({"status": "preflight_ok"})
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, Accept, Origin, Cache-Control, cache-control, X-Csrf-Token, X-CSRFToken'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Max-Age'] = '86400'
        logger.debug(f"OPTIONS request to /current_user from {origin}, responding with CORS headers")
        return response

    try:
        logger.debug(f"GET request to /current_user from {origin}")
        user_id = session.get('user_id')
        if not user_id:
            response = jsonify({
                "authenticated": False,
                "message": "No user session found"
            })
            if origin:
                response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response

        user = User.get_by_id(user_id)
        if not user:
            response = jsonify({
                "authenticated": False,
                "message": "User not found"
            })
            if origin:
                response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response

        # (Omitted: profile_image_url logic for brevity)

        response = jsonify({
            "authenticated": True,
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email if hasattr(user, 'email') else None,
                "profile_image": user.profile_image if hasattr(user, 'profile_image') else None,
                "first_name": user.first_name if hasattr(user, 'first_name') else None,
                "last_name": user.last_name if hasattr(user, 'last_name') else None
            }
        })
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

    except Exception as e:
        logger.error(f"Error in current_user: {str(e)}", exc_info=True)
        response = jsonify({
            "authenticated": False,
            "message": "Error checking authentication status"
        })
        response.status_code = 500
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

# =============================
# REGISTRATION ROUTE (React-friendly version)
# =============================
@auth.route('/register', methods=['GET', 'POST'])
@cross_origin(supports_credentials=True)
def register():
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            password2 = request.form.get('password2')
            
            # Validate required fields
            if not all([username, email, password, password2]):
                logger.info('Missing required fields')
                return jsonify({'error': 'All fields are required'}), 400
                
            # Validate passwords match
            if password != password2:
                logger.info('Passwords do not match')
                return jsonify({'error': 'Passwords do not match'}), 400
                
            # Check if username or email already exists
            if User.query.filter_by(username=username).first():
                logger.info(f'Username already exists: {username}')
                return jsonify({'error': 'Username already exists'}), 400
            if User.query.filter_by(email=email).first():
                logger.info(f'Email already exists: {email}')
                return jsonify({'error': 'Email already exists'}), 400
                
            # Handle profile photo upload
            if 'profile_photo' not in request.files:
                logger.info('Profile photo is required')
                return jsonify({'error': 'Profile photo is required'}), 400
                
            profile_photo = request.files['profile_photo']
            if not profile_photo.filename:
                logger.info('No selected file for profile photo')
                return jsonify({'error': 'No selected file'}), 400
            
            # Create new user first to get the ID
            new_user = User(
                username=username,
                email=email
            )
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            logger.info(f'Created new user: {new_user.id} ({new_user.username})')
            
            try:
                # Save profile photo using the existing function
                filename = save_profile_photo(profile_photo, new_user.id)
                logger.info(f'Saved profile photo as: {filename}')
                new_user.profile_image = filename
                db.session.commit()
                logger.info(f'Updated user {new_user.id} profile_image to {filename}')
                
                # Encode face and add to FAISS index
                face_encoding = index_profile_face(
                    os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], 'profile_photos', filename),
                    new_user.id,
                    username
                )
                logger.info(f'index_profile_face result: {face_encoding}')
                if face_encoding is None:
                    # If face encoding fails, delete the user and return error
                    db.session.delete(new_user)
                    db.session.commit()
                    logger.info('Face encoding failed, user deleted')
                    return jsonify({'error': 'Could not detect a face in the uploaded image. Please try again with a clearer photo.'}), 400
                
                # Log in the user
                login_user(new_user)
                logger.info(f'User {new_user.id} logged in after registration')
                
                response = {
                    'message': 'Registration successful',
                    'user': {
                        'id': new_user.id,
                        'username': new_user.username,
                        'email': new_user.email,
                        'profile_photo': new_user.profile_image
                    }
                }
                logger.info(f'Registration response: {response}')
                return jsonify(response), 201
                
            except Exception as e:
                # If anything fails after user creation, delete the user
                db.session.delete(new_user)
                db.session.commit()
                current_app.logger.error(f"Error processing profile photo: {str(e)}")
                return jsonify({'error': 'Error processing profile photo. Please try again.'}), 500
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Registration error: {str(e)}")
            return jsonify({'error': 'Registration failed. Please try again.'}), 500
    # For GET requests, return a 404 since we're using a SPA
    return jsonify({'error': 'Not found'}), 404

# =============================
# LOGOUT ROUTE
# =============================
@auth.route('/logout', methods=['GET', 'POST', 'OPTIONS'])
def logout():
    # Handle CORS preflight
    origin = request.headers.get('Origin', '*')
    if request.method == 'OPTIONS':
        response = jsonify({'success': True})
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

    # Actual logout logic
    logout_user()
    session.clear()
    response = jsonify({'success': True, 'message': 'Logged out'})
    response.headers['Access-Control-Allow-Origin'] = origin
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

@auth.route("/api/csrf-token", methods=["GET"])
def get_csrf_token():
    try:
        token = generate_csrf()
        return jsonify({"csrf_token": token, "message": "CSRF token generated"}), 200
    except Exception as e:
        current_app.logger.error(f"Error generating CSRF token: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to generate CSRF token"}), 500

@auth.route("/reset-password", methods=["GET", "POST"])
def reset_password_request():
    return render_template("auth/reset_password.html")

@auth.route("/account")
@login_required
def account():
    try:
        user = User.get_by_id(session.get("user_id"))
        if not user:
            session.clear()
            raise AuthenticationError("User not found")
        return render_template("auth/account.html", user=user)
    except AuthenticationError as e:
        flash(str(e), "error")
        return redirect(url_for("auth.login"))
    except Exception as e:
        logger.error(f"Account page error: {str(e)}", exc_info=True)
        flash("An error occurred", "error")
        return redirect(url_for("main.index"))

@limiter.exempt
@auth.route("/auth_status", methods=["GET", "OPTIONS"])
def auth_status():
    return current_user_info()