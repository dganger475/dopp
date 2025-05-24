"""
Direct Face View Route
=====================

This module provides simplified routes for viewing faces directly
with improved image path handling.
"""

import os
import sqlite3

from flask import (
    Blueprint,
    abort,
    current_app,
    redirect,
    render_template,
    session,
    url_for,
    send_from_directory,
    send_file
)

from models.user import User
from .config import get_image_paths, get_db_path, get_profile_image_path

direct_view = Blueprint("direct_view", __name__)


# Special route to handle filename-based direct-face URLs
@direct_view.route("/direct-face/<string:filename>")
def view_direct_face_by_filename(filename):
    """
    Serves a face image directly by filename.
    Checks all possible image paths.
    """
    current_app.logger.critical(f"--- Direct Face Route CALLED with filename: {filename} ---")
    # Prevent directory traversal attacks
    if ".." in filename or filename.startswith("/"):
        current_app.logger.warning(f"Directory traversal attempt: {filename}")
        abort(404)

    # Try all possible image paths
    possible_paths = get_image_paths(filename)
    for image_path in possible_paths:
        try:
            if os.path.exists(image_path):
                current_app.logger.info(f"Serving image from: {image_path}")
                directory = os.path.dirname(image_path)
                filename = os.path.basename(image_path)
                return send_from_directory(directory, filename)
        except Exception as e:
            current_app.logger.error(f"Error checking/serving file {filename} from {image_path}: {e}")
            continue
    
    current_app.logger.warning(f"Image file not found: {filename} in any checked directories.")
    abort(404)


@direct_view.route("/direct-face/<int:face_id>")
def view_direct_face(face_id):
    """Display a face using its ID with proper image path handling"""
    try:
        # Connect to the faces database
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()

        # Query the faces table by ID
        cursor.execute("SELECT * FROM faces WHERE id = ?", (face_id,))
        face = cursor.fetchone()

        if not face:
            current_app.logger.warning(f"Face with ID {face_id} not found in database")
            return render_template("error.html", message="Face not found"), 404

        # Get current user information
        user_id = session.get("user_id")
        if user_id:
            user = User.get_by_id(user_id)
            username = user.username
            profile_image = get_profile_image_path(user.profile_image)
        else:
            user = None
            username = "Guest"
            profile_image = get_profile_image_path(None)

        # Calculate similarity
        similarity = 85  # Default similarity
        if face and "distance" in face.keys() and face["distance"] is not None:
            threshold = 0.6
            distance = float(face["distance"])
            similarity = max(0, 100 * (1 - (distance / threshold)))
            similarity = round(similarity, 1)  # Round to 1 decimal place

        # Extract face metadata
        match_filename = face["filename"]
        decade = face["decade"] or "Unknown"
        state = face["state"] or "Unknown"

        # Get all possible paths for the face image
        possible_paths = get_image_paths(match_filename)
        match_path = None
        match_url = None

        # Try to find the first existing path
        for path in possible_paths:
            if os.path.exists(path):
                match_path = path
                # Convert to URL
                if 'static' in path:
                    match_url = '/' + os.path.relpath(path, current_app.root_path)
                else:
                    match_url = url_for('static', filename=os.path.relpath(path, os.path.join(current_app.root_path, 'static')))
                break

        # If no path found, try to find a matching profile image
        if not match_path and "school_name" in face.keys() and face["school_name"]:
            username = face["school_name"]
            if username in match_filename:
                user_with_image = User.get_by_username(username)
                if user_with_image and user_with_image.profile_image:
                    profile_path = get_profile_image_path(user_with_image.profile_image)
                    if os.path.exists(profile_path):
                        match_path = profile_path
                        if 'static' in profile_path:
                            match_url = '/' + os.path.relpath(profile_path, current_app.root_path)
                        else:
                            match_url = url_for('static', filename=os.path.relpath(profile_path, os.path.join(current_app.root_path, 'static')))

        # If still no path found, use a default URL
        if not match_url:
            match_url = url_for('static', filename=f'extracted_faces/{match_filename}')

        # Generate the response
        return render_template(
            "direct_face.html",
            face_id=face_id,
            username=username,
            profile_image=profile_image,
            match_url=match_url,
            decade=decade,
            state=state,
            similarity=similarity
        )

    except Exception as e:
        current_app.logger.error(f"Error in view_direct_face: {e}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return render_template("error.html", message="An error occurred"), 500
    finally:
        if "conn" in locals() and conn:
            conn.close()


@direct_view.route('/direct-match-image/<int:match_id>')
def get_direct_match_image(match_id):
    """Serve match images directly from any valid image path"""
    try:
        conn = sqlite3.connect(get_db_path())
        cursor = conn.cursor()
        cursor.execute("SELECT filename FROM faces WHERE id = ?", (match_id,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            current_app.logger.warning(f"No face found with ID {match_id}")
            return send_default_image()

        filename = result[0]
        possible_paths = get_image_paths(filename)
        
        for path in possible_paths:
            if os.path.exists(path):
                current_app.logger.info(f"Serving image from: {path}")
                return send_file(path, mimetype='image/jpeg')

        current_app.logger.error(f"Image not found in any location: {filename}")
        return send_default_image()

    except Exception as e:
        current_app.logger.error(f"Error in get_direct_match_image: {e}")
        return send_default_image()


def send_default_image():
    """Helper function to send the default profile image."""
    return send_file(get_profile_image_path(None), mimetype='image/png')
