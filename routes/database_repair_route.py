import logging

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    url_for,
)

from routes.auth import login_required
from utils.database_repair import backup_database, repair_users_database

db_repair = Blueprint("db_repair", __name__)


@db_repair.route("/repair", methods=["GET"])
@login_required
def repair_database():
    """
    Run database repair operations to fix issues with fields that cannot be updated.
    """
    try:
        # First, create a backup
        if not backup_database():
            flash("Database repair aborted - could not create backup", "error")
            return redirect(url_for("profile.edit_profile"))

        # Run repair operations
        success = repair_users_database()

        if success:
            flash(
                "Database repair completed successfully. Try updating your profile now.",
                "success",
            )
            current_app.logger.info("Database repair completed successfully")
        else:
            flash("Database repair failed. Please contact support.", "error")
            current_app.logger.error("Database repair failed")

        return redirect(url_for("profile.edit_profile"))

    except Exception as e:
        current_app.logger.error(f"Error during database repair: {e}")
        flash(f"Error during database repair: {str(e)}", "error")
        return redirect(url_for("profile.edit_profile"))


@db_repair.route("/status", methods=["GET"])
@login_required
def database_status():
    """
    Check database status and show information about fields.
    """
    import sqlite3

    from utils.db.database import get_users_db_connection

    try:
        conn = get_users_db_connection()
        if not conn:
            return jsonify({"error": "Could not connect to database"})

        cursor = conn.cursor()

        # Get table structure
        cursor.execute("PRAGMA table_info(users)")
        columns = [
            dict(zip(["cid", "name", "type", "notnull", "dflt_value", "pk"], row))
            for row in cursor.fetchall()
        ]

        # Check critical fields
        critical_fields = [
            "first_name",
            "last_name",
            "birthdate",
            "hometown",
            "current_location",
        ]
        critical_field_info = []

        for field in critical_fields:
            # Find in columns
            field_info = next((col for col in columns if col["name"] == field), None)

            if field_info:
                # Count records with NULL values for this field
                cursor.execute(f"SELECT COUNT(*) FROM users WHERE {field} IS NULL")
                null_count = cursor.fetchone()[0]

                # Count records with empty string
                cursor.execute(f"SELECT COUNT(*) FROM users WHERE {field} = ''")
                empty_count = cursor.fetchone()[0]

                field_info["null_count"] = null_count
                field_info["empty_count"] = empty_count

                critical_field_info.append(field_info)

        conn.close()

        return render_template(
            "database_status.html",
            columns=columns,
            critical_field_info=critical_field_info,
        )

    except Exception as e:
        current_app.logger.error(f"Error checking database status: {e}")
        return jsonify({"error": str(e)})
