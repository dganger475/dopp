import logging
import sqlite3

from flask import current_app

from utils.db.database import get_users_db_connection


def direct_update_profile_fields(user_id, field_data):
    """
    Directly update problematic profile fields using explicit SQL commands.

    Args:
        user_id (int): The user ID
        field_data (dict): Dictionary of field values to update

    Returns:
        bool: True if successful, False otherwise
    """
    conn = get_users_db_connection()
    if not conn:
        logging.error(
            f"Failed to connect to database for direct update of user {user_id}"
        )
        return False

    try:
        cursor = conn.cursor()
        logging.info(f"Direct update for user {user_id} with data: {field_data}")

        # Only include the critical fields that we know are problematic
        critical_fields = [
            "first_name",
            "last_name",
            "birthdate",
            "hometown",
            "current_location",
        ]
        valid_updates = {k: v for k, v in field_data.items() if k in critical_fields}

        if not valid_updates:
            logging.warning(f"No valid fields to update for user {user_id}")
            return True  # Nothing to update

        # Construct direct update SQL with explicit fields
        query = """
        UPDATE users 
        SET first_name = CASE WHEN :first_name IS NULL THEN first_name ELSE :first_name END,
            last_name = CASE WHEN :last_name IS NULL THEN last_name ELSE :last_name END,
            birthdate = CASE WHEN :birthdate IS NULL THEN birthdate ELSE :birthdate END,
            hometown = CASE WHEN :hometown IS NULL THEN hometown ELSE :hometown END,
            current_location = CASE WHEN :current_location IS NULL THEN current_location ELSE :current_location END
        WHERE id = :user_id
        """

        # Add user_id to parameters and ensure none of the values are None
        params = {
            "user_id": user_id,
            "first_name": valid_updates.get("first_name", ""),
            "last_name": valid_updates.get("last_name", ""),
            "birthdate": valid_updates.get("birthdate", ""),
            "hometown": valid_updates.get("hometown", ""),
            "current_location": valid_updates.get("current_location", ""),
        }

        # Replace None values with empty strings
        for key, value in params.items():
            if value is None:
                params[key] = ""

        # Execute update
        logging.info(f"Executing direct update query: {query} with params: {params}")
        cursor.execute(query, params)
        conn.commit()

        # Verify the update
        cursor.execute(
            "SELECT first_name, last_name, birthdate, hometown, current_location FROM users WHERE id = ?",
            (user_id,),
        )
        updated_data = cursor.fetchone()

        if updated_data:
            updated_dict = dict(updated_data)
            logging.info(f"User {user_id} after direct update: {updated_dict}")

            # Check if values were updated correctly
            all_updated = True
            for field, expected_value in valid_updates.items():
                actual_value = updated_dict.get(field, "")
                if expected_value != actual_value:
                    logging.error(
                        f"Direct update failed for field '{field}': expected '{expected_value}', got '{actual_value}'"
                    )
                    all_updated = False
                else:
                    logging.info(
                        f"Field '{field}' successfully updated to '{actual_value}'"
                    )

            return all_updated
        else:
            logging.error(f"Could not retrieve user {user_id} after direct update")
            return False

    except Exception as e:
        logging.error(f"Error during direct update: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
