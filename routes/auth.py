"""
Authentication Blueprint
=======================

Handles all user authentication routes with improved security and validation.
"""

# Standard Library Imports
import logging
import os
import sys
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add project root to path
PROJECT_ROOT = str(Path(__file__).parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Third-Party Imports
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
    jsonify
)
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)
from urllib.parse import urlparse as url_parse
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from flask_wtf.csrf import generate_csrf

# Project Imports
from models.user import User
from extensions import db
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

logger.info("Successfully imported all required modules for auth")

try:
    logger.info("Successfully imported all required modules for auth")
except ImportError as e:
    logger.error("Failed to import required modules: %s", str(e))
    logger.error("Python path: %s", sys.path)
    logger.error("Traceback:", exc_info=True)
    raise

# === Blueprint Definition ===
auth = Blueprint("auth", __name__)

def validate_password_strength(password):
    """Validate password meets security requirements"""
    if len(password) < current_app.config['PASSWORD_MIN_LENGTH']:
        raise ValidationError('Password must be at least 8 characters long')
    if current_app.config['PASSWORD_REQUIRE_UPPERCASE'] and not any(c.isupper() for c in password):
        raise ValidationError('Password must contain at least one uppercase letter')
    if current_app.config['PASSWORD_REQUIRE_LOWERCASE'] and not any(c.islower() for c in password):
        raise ValidationError('Password must contain at least one lowercase letter')
    if current_app.config['PASSWORD_REQUIRE_NUMBERS'] and not any(c.isdigit() for c in password):
        raise ValidationError('Password must contain at least one number')
    if current_app.config['PASSWORD_REQUIRE_SPECIAL'] and not any(not c.isalnum() for c in password):
        raise ValidationError('Password must contain at least one special character')

# =============================
# LOGIN ROUTE
# =============================
@auth.route("/login", methods=["GET", "POST"])
@rate_limit
@csrf.exempt
def login():
    """Handle user login with rate limiting and improved security"""
    try:
        # Check if user is already logged in using session
        user_id = session.get('user_id')
        if user_id:
            user = User.get_by_id(user_id)
            if user:
                return redirect(url_for("social.feed.feed_page"))

        if request.method == "POST":
            # Handle both JSON and form data
            if request.is_json:
                data = request.get_json()
                username = sanitize_input(data.get("username"))
                password = data.get("password")
            else:
                form = LoginForm()
                if form.validate_on_submit():
                    email = sanitize_input(form.email.data)  # Using email field from form
                    password = form.password.data
                else:
                    return render_template("login.html", title="Login", form=form)

            if request.is_json:
                if not username or not password:
                    raise ValidationError("Username and password are required")
                user = User.get_by_username(username)
            else:
                if not email or not password:
                    raise ValidationError("Email and password are required")
                user = User.get_by_email(email)
            
            if not user or not user.verify_password(password):
                # Increment failed login attempts
                key = f'login_attempts:{request.remote_addr}'
                attempts = increment_cache_value(key, timeout=3600)  # 1 hour timeout
                
                if attempts >= 5:
                    raise AuthenticationError("Too many failed attempts. Please try again later.")
                
                if request.is_json:
                    raise AuthenticationError("Invalid username or password")
                flash("Invalid email or password", "error")
                return render_template("login.html", title="Login", form=LoginForm())

            # Reset failed login attempts
            delete_cache_value(f'login_attempts:{request.remote_addr}')

            login_user(user)
            session["user_id"] = user.id
            session.permanent = True
            
            # Log successful login
            logger.info(f"User {user.username} logged in successfully", extra={'user_id': user.id})
            
            # Trigger FAISS index rebuild after successful login
            try:
                from utils.face.recognition import rebuild_faiss_index
                current_app.logger.info(f"Triggering FAISS index rebuild on login for user {user.username}")
                # Run the rebuild in a non-blocking way
                rebuild_success = rebuild_faiss_index(app=current_app)
                if rebuild_success:
                    current_app.logger.info("FAISS index rebuilt successfully on login")
                else:
                    current_app.logger.warning("FAISS index rebuild failed on login")
            except Exception as e:
                current_app.logger.error(f"Error during FAISS index rebuild on login: {e}", exc_info=True)
            
            # Redirect to next page or default to feed
            return redirect(url_for("social.feed.feed_page"))

        return render_template("login.html", title="Login", form=LoginForm())

    except (ValidationError, AuthenticationError) as e:
        logger.warning(f"Login failed: {str(e)}", 
                      extra={'ip': request.remote_addr})
        if request.is_json:
            return jsonify({"error": str(e)}), 401
        flash(str(e), "error")
        return render_template("login.html", title="Login", form=LoginForm()), 401
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True,
                    extra={'ip': request.remote_addr})
        if request.is_json:
            return jsonify({"error": "An internal error occurred"}), 500
        flash("An error occurred during login", "error")
        return render_template("login.html", title="Login", form=LoginForm()), 500

# =============================
# CURRENT USER CHECK
# =============================
@auth.route("/current_user", methods=["GET"])
def current_user():
    """Check if user is authenticated and return user info"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"authenticated": False}), 401

        user = User.get_by_id(user_id)
        if not user:
            return jsonify({"authenticated": False}), 401

        return jsonify({
            "authenticated": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        })

    except Exception as e:
        logger.error(f"Current user check error: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to check authentication"}), 500

# =============================
# REGISTRATION ROUTE
# =============================
@auth.route("/register", methods=["GET", "POST"])
@rate_limit
def register():
    """Handle user registration with improved validation and security"""
    try:
        if current_user.is_authenticated:
            return redirect(url_for("social.feed.feed_page"))

        form = RegisterForm()

        if form.validate_on_submit():
            username = sanitize_input(form.username.data.strip())
            email = sanitize_input(form.email.data.strip().lower())
            password = form.password.data
            profile_photo = form.profile_photo.data

            # Validate password strength
            validate_password_strength(password)

            # Check for existing user
            if User.get_by_username(username) or User.get_by_email(email):
                raise ValidationError("Username or email already exists")

            # Create user
            user = User.create(
                username=username,
                email=email,
                password=password
            )

            if not user:
                raise ValidationError("Failed to create user")

            # Handle profile photo
            if profile_photo:
                try:
                    filename = save_profile_photo(profile_photo, user.id)
                    if filename:
                        user.update(profile_image=filename)
                        index_profile_face(filename, user.id, username)
                except FileUploadError as e:
                    logger.warning(f"Profile photo upload failed: {str(e)}")
                    flash("Could not process profile photo. Using default image.", "warning")

            # Set default profile image if none provided
            if not user.profile_image:
                default_image = os.path.basename(get_default_profile_image_path())
                user.update(profile_image=default_image)

            login_user(user)
            session['user_id'] = user.id
            session.permanent = True

            logger.info(f"User registered successfully: {username}",
                       extra={'user_id': user.id})

            return redirect(url_for("social.feed.feed_page"))

        return render_template("register.html", form=form)

    except ValidationError as e:
        flash(str(e), "error")
        return render_template("register.html", form=form), 400
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        flash("An error occurred during registration", "error")
        return render_template("register.html", form=form), 500

# =============================
# LOGOUT ROUTE
# =============================
@auth.route("/logout")
@login_required
def logout():
    """Handle user logout"""
    try:
        user_id = current_user.id
        logout_user()
        session.clear()
        logger.info(f"User logged out", extra={'user_id': user_id})
        flash("You have been logged out", "info")
    except Exception as e:
        logger.error(f"Logout error: {str(e)}", exc_info=True)
        flash("An error occurred during logout", "error")
    
    return redirect(url_for("auth.login"))

@auth.route("/api/csrf-token", methods=["GET"])
def get_csrf_token():
    """API endpoint to fetch a CSRF token."""
    try:
        token = generate_csrf()
        return jsonify({"csrf_token": token, "message": "CSRF token generated"}), 200
    except Exception as e:
        current_app.logger.error(f"Error generating CSRF token: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to generate CSRF token"}), 500

# =============================
# PASSWORD RESET ROUTE
# =============================
@auth.route("/reset-password", methods=["GET", "POST"])
def reset_password_request():
    return render_template("reset_password.html")

# =============================
# ACCOUNT SETTINGS ROUTE
# =============================
@auth.route("/account")
@login_required
def account():
    """Handle account page access"""
    try:
        user = User.get_by_id(session.get("user_id"))
        if not user:
            session.clear()
            raise AuthenticationError("User not found")
        
        return render_template("account.html", user=user)
    
    except AuthenticationError as e:
        flash(str(e), "error")
        return redirect(url_for("auth.login"))
    except Exception as e:
        logger.error(f"Account page error: {str(e)}", exc_info=True)
        flash("An error occurred", "error")
        return redirect(url_for("main.index"))

# =============================
# GET CURRENT USER ROUTE (API)
# =============================
@auth.route("/current_user", methods=["GET"])
def get_current_user():
    """Get current user information using session-based authentication."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Not authenticated", "success": False}), 401

        user = User.get_by_id(user_id)
        if not user:
            # This case might happen if user_id in session is stale (e.g., user deleted)
            session.pop('user_id', None) # Clear stale session
            return jsonify({"error": "User not found or session invalid", "success": False}), 401
        
        # Format profile image URL properly
        profile_image_url = None
        if hasattr(user, 'profile_image') and user.profile_image:
            # Get the raw profile image path
            raw_path = user.profile_image
            
            # Determine the correct location of the profile image
            if raw_path.startswith('/static/'):
                # Already starts with /static/ - use as is
                profile_image_url = url_for('static', filename=raw_path[8:]) # Remove '/static/' prefix
            elif raw_path.startswith('/profile_pics/') or raw_path.startswith('profile_pics/'):
                # Strip leading slash if present and add to static URL
                clean_path = raw_path.lstrip('/')
                profile_image_url = url_for('static', filename=clean_path)
            elif '/' not in raw_path:
                # If it's just a filename with no path, assume it's in profile_pics
                profile_image_url = url_for('static', filename=f'profile_pics/{raw_path}')
            else:
                # Use as is if it's already a full URL
                profile_image_url = raw_path
                
            # Add host to URL if it's relative
            if profile_image_url.startswith('/'):
                # This ensures the image path has the full host, which the React app needs
                host = request.host_url.rstrip('/')
                profile_image_url = f"{host}{profile_image_url}"
        else:
            # Default image as a full URL with host
            default_img_url = url_for('static', filename='images/default_profile.jpg')
            host = request.host_url.rstrip('/')
            profile_image_url = f"{host}{default_img_url}"
            
        return jsonify({
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "profile_image": user.profile_image if hasattr(user, 'profile_image') else None,
                "profile_image_url": profile_image_url, # Add formatted URL
                "first_name": user.first_name if hasattr(user, 'first_name') else None,
                "last_name": user.last_name if hasattr(user, 'last_name') else None
            }
        }), 200
    except Exception as e:
        logger.error(f"API error in get_current_user: {str(e)}", exc_info=True)
        return jsonify({"error": "An internal error occurred", "success": False}), 500
