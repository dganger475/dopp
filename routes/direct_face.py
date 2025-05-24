import os
import sqlite3

from flask import Blueprint, current_app, render_template, session
from .config import get_db_path, get_profile_image_path

direct_face = Blueprint("direct_face", __name__)


@direct_face.route("/direct-face/<int:face_id>")
def view_direct_face(face_id):
    """Display a face using its ID directly from the faces table with a simplified template"""
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
            from models.user import User

            user = User.get_by_id(user_id)

            # Make sure profile_image doesn't have a leading slash
            if user.profile_image:
                user.profile_image = get_profile_image_path(user.profile_image)
        else:
            # Create a basic user object for non-logged-in users
            user = {"username": "Guest", "profile_image": get_profile_image_path(None)}

        # Calculate similarity
        similarity = 85  # Default similarity if none available

        # If we have distance data in the face entry, calculate properly
        if face and "distance" in face.keys() and face["distance"] is not None:
            threshold = 0.6  # Fixed threshold
            distance = float(face["distance"])
            similarity = max(0, 100 * (1 - (distance / threshold)))
            similarity = round(similarity, 1)  # Round to 1 decimal place

        # Format the match data for the template
        match_data = {
            "match_id": face_id,
            "filename": face["filename"],
            "decade": face["decade"] or "2010s",  # Use default if missing
            "state": face["state"] or "Unknown",  # Use default if missing
            "similarity": similarity,
        }

        # Use our new simplified template
        return render_template("direct_face.html", user=user, match_data=match_data)

    except Exception as e:
        current_app.logger.error(f"Error displaying direct face: {e}")
        import traceback

        current_app.logger.error(traceback.format_exc())
        return render_template("error.html", message="An error occurred"), 500
    finally:
        if "conn" in locals() and conn:
            conn.close()
