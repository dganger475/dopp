"""
Main Site Blueprint
==================

Handles the landing page, about, contact, help, privacy, terms, and other general site routes.
Renders templates such as home.html, about.html, contact.html, etc.

Notes:
- All business logic is delegated to models or utility functions.
- No business logic in routes; routes only handle request/response and session.
"""

# === Standard Library Imports ===
from datetime import datetime, timedelta

import jwt

# === Third-Party Imports ===
from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from models.social import ClaimedProfile, Post

# === Project Imports ===
from models.user import User
# from routes.social import create_post as social_create_post
from routes.social import social

# === Blueprint Definition ===
main = Blueprint("main", __name__)


# =============================
# PROXY ROUTES
# =============================
@main.route("/create_post", methods=["POST"])
def create_post_proxy():
    """
    Proxy route to create a post, delegating to the social blueprint's create_post.
    """
    return social_create_post()


# =============================
# DISCOVER ROUTE
# =============================
@main.route("/search/discover")
def discover():
    """
    Discover page: shows historical faces, claimed profiles, and more. Requires login.
    """
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("auth.login"))
    # Sample data for demonstration; replace with real queries later
    sections = [
        {
            "title": "Popular Historical Faces",
            "description": "Browse some of the most viewed faces in our archive.",
            "faces": [],
        },
        {
            "title": "Recently Claimed Profiles",
            "description": "See who recently claimed their historical lookalike.",
            "profiles": [],
        },
        {
            "title": "Decades",
            "description": "Jump into a specific decade to explore faces from that era.",
            "decades": ["1950s", "1960s", "1970s", "1980s", "1990s", "2000s"],
        },
        {
            "title": "Faces of the Day",
            "description": "A fresh set of faces to discover every day!",
            "faces": [],
        },
    ]
    return render_template("discover.html", sections=sections)


# =============================
# HOME/FEED ROUTE
# =============================
@main.route("/")
def index():
    """
    Home page of the application.
    Redirects to login/register page when not logged in.
    Redirects to social feed when logged in for consistent UI.
    """
    from flask_login import current_user
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    
    # Redirect to the social feed to maintain consistent UI 
    # This ensures the same template with the same context variables is used
    return redirect(url_for("social.feed.feed_page"))


# =============================
# GENERAL STATIC PAGES
# =============================
@main.route("/about")
def about():
    """
    About page.
    """
    return render_template("about.html")


@main.route("/privacy")
def privacy():
    """
    Privacy policy page.
    """
    return render_template("privacy.html")


# =============================
# MOBILE ROUTES
# =============================
@main.route("/mobile")
def mobile():
    """
    Mobile web interface.
    Always serves the mobile template for this route.
    """
    return render_template("mobile.html")


@main.route("/mobile-login", methods=["POST"])
def mobile_login():
    """
    Simplified login endpoint for mobile web interface.
    Returns a JWT token and user info on success. Uses logger for important events.
    """
    data = request.json
    current_app.logger.info(f"Mobile login attempt with data: {data}")

    if not data or not data.get("email") or not data.get("password"):
        return (
            jsonify({"message": "Email and password are required", "success": False}),
            400,
        )

    email = data.get("email")
    password = data.get("password")

    # Get user from database
    user = User.get_by_email(email)

    if not user:
        current_app.logger.warning(f"User not found for email: {email}")
        return jsonify({"message": "User not found", "success": False}), 401

    current_app.logger.info(f"User found: {user.username}, ID: {user.id}")

    # Check password
    password_valid = check_password_hash(user.password_hash, password)
    current_app.logger.info(f"Password valid: {password_valid}")

    if not password_valid:
        return jsonify({"message": "Invalid password", "success": False}), 401

    # Generate a simple token
    # Ensure 'JWT_SECRET_KEY' is set in your Flask app configuration!
    jwt_secret = current_app.config.get("JWT_SECRET_KEY")
    if not jwt_secret:
        current_app.logger.error(
            "JWT_SECRET_KEY is not set in the application configuration!"
        )
        return jsonify({"message": "Server configuration error", "success": False}), 500

    token = jwt.encode(
        {"user_id": user.id, "exp": datetime.utcnow() + timedelta(days=7)},
        jwt_secret,
        algorithm="HS256",
    )

    # Return success response
    return jsonify(
        {
            "success": True,
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "profile_image": user.profile_image,
                "first_name": user.first_name if hasattr(user, "first_name") else "",
                "last_name": user.last_name if hasattr(user, "last_name") else "",
            },
        }
    )


@main.route("/terms")
def terms():
    """Terms of service page."""
    return render_template("terms.html")


@main.route("/help")
def help():
    """Help page."""
    return render_template("help.html")
