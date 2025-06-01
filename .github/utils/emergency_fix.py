import logging
import os
import sqlite3

from flask import current_app

from utils.db.database import DEFAULT_DB_PATH


def fix_user_fields(user_id, fields_to_update):
    """
    Emergency fix for updating specific user fields using raw SQL.
    This bypasses all ORM layers and directly modifies the database.

    Args:
        user_id (int): User ID to update
        fields_to_update (dict): Fields and values to update

    Returns:
        bool: Success status
    """
    logging.info(
        f"EMERGENCY FIX: Updating fields for user {user_id}: {fields_to_update}"
    )

    # Get database path
    try:
        db_path = current_app.config.get("DB_PATH", DEFAULT_DB_PATH)
    except RuntimeError:
        db_path = DEFAULT_DB_PATH

    # Connect directly to SQLite
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Debug: Get current field values
        cursor.execute(
            """
        SELECT id, first_name, last_name, birthdate, hometown, current_location_city, current_location_state 
        FROM users WHERE id = ?
        """,
            (user_id,),
        )
        before_update = cursor.fetchone()

        if not before_update:
            logging.error(f"User {user_id} not found in database")
            return False

        logging.info(f"Before update: {dict(before_update)}")

        # Create individual update statements for each field
        for field, value in fields_to_update.items():
            if field not in [
                "first_name",
                "last_name",
                "birthdate",
                "hometown",
                "current_location_city",
                "current_location_state",
            ]:
                continue

            # Replace None with empty string
            if value is None:
                value = ""

            try:
                # Use raw update for each field individually
                query = f"UPDATE users SET {field} = ? WHERE id = ?"
                cursor.execute(query, (value, user_id))
                affected = cursor.rowcount
                logging.info(f"Direct update of {field}: affected {affected} row(s)")
            except sqlite3.Error as e:
                logging.error(f"Error updating {field}: {e}")
                return False

        # Commit changes
        conn.commit()

        # Verify changes
        cursor.execute(
            """
        SELECT id, first_name, last_name, birthdate, hometown, current_location_city, current_location_state 
        FROM users WHERE id = ?
        """,
            (user_id,),
        )
        after_update = cursor.fetchone()

        if after_update:
            after_dict = dict(after_update)
            logging.info(f"After update: {after_dict}")

            # Check if all fields were updated correctly
            success = True
            for field, expected in fields_to_update.items():
                if field in after_dict:
                    if expected is None:
                        expected = ""
                    actual = after_dict[field]
                    if expected != actual:
                        logging.error(
                            f"Field {field} was not updated correctly. Expected: '{expected}', Got: '{actual}'"
                        )
                        success = False

            return success
        else:
            logging.error(f"Could not retrieve user {user_id} after update")
            return False

    except Exception as e:
        logging.error(f"Emergency fix failed: {e}")
        return False
    finally:
        if "conn" in locals():
            conn.close()


def reset_field_defaults():
    """
    Reset all field defaults in the database to ensure proper types.
    """
    import traceback

    # Log the full stack trace to see where this is being called from
    logging.info("EMERGENCY FIX: Resetting field defaults in users table")
    stack_trace = "\n".join(traceback.format_stack())
    logging.info(f"reset_field_defaults() was called from:\n{stack_trace}")

    # Get database path
    try:
        db_path = current_app.config.get("DB_PATH", DEFAULT_DB_PATH)
    except RuntimeError:
        db_path = DEFAULT_DB_PATH

    # Connect directly to SQLite
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all users with problematic fields
        cursor.execute(
            """
        SELECT id, first_name, last_name, birthdate, hometown, current_location
        FROM users
        """
        )
        users = cursor.fetchall()

        for user in users:
            user_dict = dict(user)
            user_id = user_dict["id"]

            # Initialize fields that are NULL with empty strings
            updates = {}
            for field in [
                "first_name",
                "last_name",
                "birthdate",
                "hometown",
                "current_location",
            ]:
                if user_dict.get(field) is None:
                    updates[field] = ""

            if updates:
                logging.info(f"Fixing NULL fields for user {user_id}: {updates}")
                placeholders = ", ".join([f"{field} = ?" for field in updates.keys()])
                values = list(updates.values())
                values.append(user_id)

                query = f"UPDATE users SET {placeholders} WHERE id = ?"
                cursor.execute(query, values)

        conn.commit()
        logging.info("Field defaults reset successfully")
        return True

    except Exception as e:
        logging.error(f"Error resetting field defaults: {e}")
        return False
    finally:
        if "conn" in locals():
            conn.close()
