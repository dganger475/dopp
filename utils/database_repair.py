import logging
import os
import sqlite3

from utils.db.database import DEFAULT_DB_PATH, get_db_connection


def repair_users_database():
    """
    Repair and validate the users database to ensure all required fields exist
    and have the correct types.
    """
    logging.info("Starting database repair process")
    conn = get_db_connection()

    if not conn:
        logging.error("Could not connect to users database for repair")
        return False

    try:
        cursor = conn.cursor()

        # Check existing table structure
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = {col[1]: col[2] for col in cursor.fetchall()}

        logging.info(f"Existing columns in users table: {existing_columns}")

        # Define expected columns and their types
        expected_columns = {
            "id": "INTEGER",
            "username": "TEXT",
            "email": "TEXT",
            "password_hash": "TEXT",
            "first_name": "TEXT",
            "last_name": "TEXT",
            "bio": "TEXT",
            "hometown": "TEXT",
            "current_location": "TEXT",
            "birthdate": "TEXT",
            "website": "TEXT",
            "interests": "TEXT",
            "profile_image": "TEXT",
            "cover_photo": "TEXT",
            "profile_visibility": "TEXT",
            "share_real_name": "INTEGER",
            "share_location": "INTEGER",
            "share_age": "INTEGER",
            "created_at": "TIMESTAMP",
        }

        # Check for missing columns
        missing_columns = {
            col: dtype
            for col, dtype in expected_columns.items()
            if col not in existing_columns
        }

        # Check for type mismatches
        type_mismatches = {
            col: (existing_type, expected_columns[col])
            for col, existing_type in existing_columns.items()
            if col in expected_columns and existing_type != expected_columns[col]
        }

        if missing_columns:
            logging.warning(f"Missing columns detected: {missing_columns}")
            # Add missing columns
            for col_name, col_type in missing_columns.items():
                try:
                    cursor.execute(
                        f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"
                    )
                    logging.info(f"Added missing column: {col_name} ({col_type})")
                except sqlite3.Error as e:
                    logging.error(f"Error adding column {col_name}: {e}")

        if type_mismatches:
            logging.warning(f"Column type mismatches detected: {type_mismatches}")
            # To fix type mismatches, we need to create a new table and migrate data
            # This is a more complex operation
            if type_mismatches:
                repair_table_structure(conn, existing_columns, expected_columns)

        # Verify data integrity for critical fields
        verify_critical_fields(conn)

        conn.commit()
        logging.info("Database repair completed successfully")
        return True

    except Exception as e:
        logging.error(f"Error during database repair: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def repair_table_structure(conn, existing_columns, expected_columns):
    """
    Repair table structure by creating a new table with correct column types
    and migrating data.
    """
    cursor = conn.cursor()

    try:
        # Create temporary table with correct structure
        create_sql = """
        CREATE TABLE users_new (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            bio TEXT,
            hometown TEXT,
            current_location TEXT,
            birthdate TEXT,
            website TEXT,
            interests TEXT,
            profile_image TEXT,
            cover_photo TEXT,
            profile_visibility TEXT DEFAULT 'public',
            share_real_name INTEGER DEFAULT 0,
            share_location INTEGER DEFAULT 0,
            share_age INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        cursor.execute(create_sql)

        # Get existing column names to copy
        valid_cols = [col for col in existing_columns.keys() if col in expected_columns]
        cols_str = ", ".join(valid_cols)

        # Copy data to new table
        cursor.execute(
            f"INSERT INTO users_new ({cols_str}) SELECT {cols_str} FROM users"
        )

        # Drop old table and rename new one
        cursor.execute("DROP TABLE users")
        cursor.execute("ALTER TABLE users_new RENAME TO users")

        logging.info("Table structure successfully repaired")

    except sqlite3.Error as e:
        logging.error(f"Error repairing table structure: {e}")
        raise


def verify_critical_fields(conn):
    """
    Verify that critical fields have proper values and are not NULL
    when they should be empty strings.
    """
    cursor = conn.cursor()

    critical_fields = [
        "first_name",
        "last_name",
        "birthdate",
        "hometown",
        "current_location",
    ]

    try:
        # Get users with NULL values in critical fields
        for field in critical_fields:
            cursor.execute(f"SELECT id FROM users WHERE {field} IS NULL")
            null_field_users = cursor.fetchall()

            if null_field_users:
                user_ids = [row[0] for row in null_field_users]
                logging.warning(f"Users with NULL {field}: {user_ids}")

                # Fix NULL values by setting them to empty string
                cursor.execute(f"UPDATE users SET {field} = '' WHERE {field} IS NULL")
                logging.info(f"Fixed {cursor.rowcount} NULL values in {field}")

    except sqlite3.Error as e:
        logging.error(f"Error verifying critical fields: {e}")
        raise


def backup_database():
    """Create a backup of the users database before repairs."""
    try:
        if os.path.exists(DEFAULT_DB_PATH):
            backup_path = f"{DEFAULT_DB_PATH}.bak"
            with open(DEFAULT_DB_PATH, "rb") as src, open(
                backup_path, "wb"
            ) as dst:
                dst.write(src.read())
            logging.info(f"Database backup created at {backup_path}")
            return True
    except Exception as e:
        logging.error(f"Error creating database backup: {e}")
    return False


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Create backup
    if backup_database():
        # Repair database
        repair_users_database()
    else:
        logging.error("Database repair aborted due to backup failure")
