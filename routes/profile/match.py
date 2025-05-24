
from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify, flash, current_app
import os, traceback, secrets, time
from werkzeug.utils import secure_filename
from routes.auth import login_required
from models.user import User
from utils.image_paths import get_image_path, normalize_profile_image_path
from forms.profile_forms import ProfileEditForm

match = Blueprint('match', __name__)

from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify, flash, current_app
import os, traceback, secrets, time
from werkzeug.utils import secure_filename

match = Blueprint('match', __name__)


def update_match_privacy():
    """
    Update privacy settings for a match.
    - Only allows the owner of the match to update privacy.
    - Returns JSON response for AJAX/frontend handling.
    """
    user_id = session.get("user_id")
    match_id = request.form.get("match_id")
    privacy_level = request.form.get("privacy_level")

    if (
        not match_id
        or not privacy_level
        or privacy_level not in ("public", "friends", "private")
    ):
        return jsonify({"success": False, "message": "Invalid request parameters"})

    # Get the match
    from models.user_match import UserMatch

    match = UserMatch.get_by_id(match_id)

    # Verify ownership
    if not match or str(match.user_id) != str(user_id):
        return jsonify(
            {"success": False, "message": "Match not found or access denied"}
        )

    # Update privacy
    if match.set_privacy(privacy_level):
        return jsonify(
            {
                "success": True,
                "message": f"Privacy updated to {privacy_level}",
                "privacy_level": privacy_level,
            }
        )
    else:
        return jsonify({"success": False, "message": "Failed to update privacy level"})


@profile.route("/like_match/<int:match_id>", methods=["POST"])
@login_required
def like_match(match_id):
    """
    Toggle like for a match and return updated like state and count.
    - Allows a user to like/unlike a match (face) and returns the new state and like count.
    - Returns JSON response for AJAX/frontend use.
    """
    from models.user_match import UserMatch

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    match = UserMatch.get_by_match_id(match_id)
    if not match or not match.face_id:
        return jsonify({"success": False, "error": "Invalid match ID"}), 400
    # Toggle like
    liked = UserMatch.toggle_like(user_id, match.face_id)
    like_count = UserMatch.count_likes(match.face_id)

    # Notify match owner if not liking own match
    if match.user_id != user_id:
        from models.notification import Notification
        Notification.create(
            user_id=match.user_id,
            type=Notification.TYPE_LIKE if hasattr(Notification, 'TYPE_LIKE') else 'like',
            content="Your match card was liked!",
            entity_id=match.id,
            entity_type="match",
            sender_id=user_id
        )
    return jsonify({"success": True, "liked": liked, "like_count": like_count})


@profile.route("/matches/bulk-privacy", methods=["POST"])
@login_required
def update_bulk_match_privacy():
    """Update privacy settings for multiple matches."""
    user_id = session.get("user_id")
    privacy_level = request.form.get("privacy_level")
    match_ids = request.form.getlist("match_ids[]")

    if (
        not match_ids
        or not privacy_level
        or privacy_level not in ("public", "friends", "private")
    ):
        return jsonify({"success": False, "message": "Invalid request parameters"})

    from models.user_match import UserMatch

    success_count = 0
    failed_count = 0

    for match_id in match_ids:
        # Get the match
        match = UserMatch.get_by_id(match_id)

        # Verify ownership
        if not match or str(match.user_id) != str(user_id):
            failed_count += 1
            continue

        # Update privacy
        if match.set_privacy(privacy_level):
            success_count += 1
        else:
            failed_count += 1

    return jsonify(
        {
            "success": True,
            "message": f"Updated {success_count} matches to {privacy_level} privacy. {failed_count} failed.",
            "privacy_level": privacy_level,
            "success_count": success_count,
            "failed_count": failed_count,
        }
    )