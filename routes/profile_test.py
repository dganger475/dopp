import json
import logging
import os

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

from models.user import User
from routes.auth import login_required

profile_test = Blueprint("profile_test", __name__)


@profile_test.route("/verify_profile_update", methods=["GET", "POST"])
@login_required
def verify_profile_update():
    """Test endpoint to verify profile updates are working correctly."""
    user_id = session.get("user_id")

    # Get the user
    user = User.get_by_id(user_id)
    if not user:
        return jsonify(
            {"success": False, "message": "User not found", "user_id": user_id}
        )

    if request.method == "POST":
        # Get form data with fallbacks
        updates = {}
        fields_to_test = [
            "bio",
            "hometown",
            "current_location",
            "first_name",
            "last_name",
            "website",
            "interests",
        ]

        for field in fields_to_test:
            if field in request.form:
                updates[field] = request.form.get(field)

        # Log what we're going to update
        current_app.logger.info(f"Test update for user {user_id}: {updates}")

        # Attempt the update
        try:
            # Store original values for comparison
            original_values = {
                field: getattr(user, field, None) for field in fields_to_test
            }

            # Perform update
            update_success = user.update(**updates)

            # Get the updated user
            updated_user = User.get_by_id(user_id)

            # Compare values
            new_values = {
                field: getattr(updated_user, field, None) for field in fields_to_test
            }
            comparison = []

            for field in fields_to_test:
                if field in updates:
                    comparison.append(
                        {
                            "field": field,
                            "original": original_values.get(field),
                            "expected": updates.get(field),
                            "actual": new_values.get(field),
                            "success": new_values.get(field) == updates.get(field),
                        }
                    )

            return jsonify(
                {
                    "success": update_success,
                    "message": "Profile update test completed",
                    "comparison": comparison,
                    "all_fields_updated_correctly": all(
                        item["success"] for item in comparison if field in updates
                    ),
                }
            )

        except Exception as e:
            current_app.logger.error(f"Error in profile update test: {e}")
            return jsonify(
                {
                    "success": False,
                    "message": f"Error during update: {str(e)}",
                    "user_id": user_id,
                }
            )

    # GET request: render test form
    return render_template("profile_test.html", user=user)


@profile_test.route("/debug_user_info")
@login_required
def debug_user_info():
    """Return detailed user info for debugging."""
    user_id = session.get("user_id")

    # Get the user
    user = User.get_by_id(user_id)
    if not user:
        return jsonify(
            {"success": False, "message": "User not found", "user_id": user_id}
        )

    # Get all user attributes that aren't private
    user_info = {}
    for attr in dir(user):
        # Skip private attributes and methods
        if attr.startswith("_") or callable(getattr(user, attr)):
            continue

        # Skip sensitive fields
        if attr in ["password_hash"]:
            continue

        user_info[attr] = getattr(user, attr)

    # Get database table info
    try:
        conn = user._get_db_connection()
        cursor = conn.cursor()

        # Get table structure
        cursor.execute("PRAGMA table_info(users)")
        columns = [dict(col) for col in cursor.fetchall()]

        # Get actual row data
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()

        if row:
            row_data = dict(row)
        else:
            row_data = None

        conn.close()

        return jsonify(
            {
                "success": True,
                "user_info": user_info,
                "table_columns": columns,
                "database_row": row_data,
            }
        )

    except Exception as e:
        current_app.logger.error(f"Error in debug user info: {e}")
        return jsonify(
            {
                "success": False,
                "message": f"Error fetching debug info: {str(e)}",
                "user_info": user_info,
            }
        )
