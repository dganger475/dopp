
from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify, flash, current_app
import os, traceback, secrets, time
from werkzeug.utils import secure_filename
from routes.auth import login_required
from models.user import User
from utils.image_paths import get_image_path, normalize_profile_image_path
from forms.profile_forms import ProfileEditForm

follow = Blueprint('follow', __name__)

from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify, flash, current_app
import os, traceback, secrets, time
from werkzeug.utils import secure_filename

follow = Blueprint('follow', __name__)


def follow_user(user_id):
    """
    Follow a user and create a notification for the followed user.
    - Checks if already following; if not, adds the follower relationship.
    - Creates a notification using SQLAlchemy ORM.
    - Returns JSON response for frontend handling.
    Robust error handling and DB connection management.
    """
    try:
        # Get current user
        current_user_id = session.get("user_id")
        if not current_user_id:
            return jsonify({"error": "Not logged in"}), 401

        # Check if already following
        conn = get_users_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM followers WHERE follower_id = ? AND following_id = ?",
            (current_user_id, user_id),
        )
        if cursor.fetchone():
            return jsonify({"error": "Already following this user"}), 400

        # Add follower relationship
        cursor.execute(
            "INSERT INTO followers (follower_id, following_id) VALUES (?, ?)",
            (current_user_id, user_id),
        )

        # Create notification for the followed user
        notification = Notification(
            user_id=user_id,
            type="follow",
            from_user_id=current_user_id,
            created_at=datetime.utcnow(),
        )
        db.session.add(notification)
        db.session.commit()

        conn.commit()
        return jsonify({"message": "Successfully followed user"}), 200

    except Exception as e:
        current_app.logger.error(f"Error following user: {str(e)}")
        return jsonify({"error": "An error occurred"}), 500
    finally:
        if "conn" in locals():
            conn.close()


@profile.route("/unfollow/<int:user_id>", methods=["POST"])
@login_required
def unfollow_user(user_id):
    """
    Unfollow a user.
    - Removes the follower relationship from the followers table.
    - Returns JSON response for frontend handling.
    Robust error handling and DB connection management.
    """
    try:
        current_user_id = session.get("user_id")
        if not current_user_id:
            return jsonify({"error": "Not logged in"}), 401

        conn = get_users_db_connection()
        cursor = conn.cursor()

        # Remove follower relationship
        cursor.execute(
            "DELETE FROM followers WHERE follower_id = ? AND following_id = ?",
            (current_user_id, user_id),
        )

        if cursor.rowcount == 0:
            return jsonify({"error": "Not following this user"}), 400

        conn.commit()
        return jsonify({"message": "Successfully unfollowed user"}), 200

    except Exception as e:
        current_app.logger.error(f"Error unfollowing user: {str(e)}")
        return jsonify({"error": "An error occurred"}), 500
    finally:
        if "conn" in locals():
            conn.close()


@profile.route("/settings")
@login_required