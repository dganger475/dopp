"""
Database Migrations
=================

Handles database schema updates and migrations.
"""

import logging
from utils.db.database import get_db_connection

logger = logging.getLogger(__name__)

def migrate_city_state():
    """Add city and state columns to users table."""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database for city/state migration")
        return False

    cursor = conn.cursor()
    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add current_location_city if it doesn't exist
        if 'current_location_city' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN current_location_city TEXT')
            logger.info("Added current_location_city column")
            
        # Add current_location_state if it doesn't exist
        if 'current_location_state' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN current_location_state TEXT')
            logger.info("Added current_location_state column")
            
        # Migrate data from current_location if needed
        if 'current_location' in columns:
            cursor.execute('UPDATE users SET current_location_city = current_location')
            logger.info("Migrated data from current_location to current_location_city")
            
        conn.commit()
        logger.info("City/state migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during city/state migration: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

def migrate_face_filename():
    """Add face_filename column to users table."""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database for face_filename migration")
        return False

    cursor = conn.cursor()
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add face_filename if it doesn't exist
        if 'face_filename' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN face_filename TEXT')
            logger.info("Added face_filename column")
            
        conn.commit()
        logger.info("Face filename migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during face_filename migration: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

def migrate_user_face_encoding():
    """Add face_encoding BLOB column to users table if it doesn't exist."""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database for user face_encoding migration")
        return False

    cursor = conn.cursor()
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add face_encoding if it doesn't exist
        if 'face_encoding' not in columns:
            cursor.execute('ALTER TABLE users ADD COLUMN face_encoding BLOB')
            logger.info("Added face_encoding BLOB column to users table")
        
        conn.commit()
        logger.info("User face_encoding migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during user face_encoding migration: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

def migrate_claimed_profiles_add_claimed_at():
    """Add claimed_at column to claimed_profiles table if it doesn't exist."""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database for claimed_profiles.claimed_at migration")
        return False

    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(claimed_profiles)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'claimed_at' not in columns:
            cursor.execute('ALTER TABLE claimed_profiles ADD COLUMN claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            logger.info("Added claimed_at column to claimed_profiles table")
        
        conn.commit()
        logger.info("Claimed_profiles.claimed_at migration completed successfully (or already up-to-date).")
        return True
        
    except Exception as e:
        logger.error(f"Error during claimed_profiles.claimed_at migration: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()

def run_migrations():
    """Run all pending migrations."""
    try:
        # Run city/state migration
        if migrate_city_state():
            logger.info("Database migration for city/state applied successfully (or already up-to-date).")
        else:
            logger.error("Failed to apply city/state migration.")
            
        # Run face_filename migration
        if migrate_face_filename():
            logger.info("Database migration for face_filename applied successfully (or already up-to-date).")
        else:
            logger.error("Failed to apply face_filename migration.")
            
        # Run user face_encoding migration
        if migrate_user_face_encoding():
            logger.info("Database migration for user face_encoding applied successfully (or already up-to-date).")
        else:
            logger.error(f"Failed to apply user face_encoding migration.")

        # Run claimed_profiles.claimed_at migration
        if migrate_claimed_profiles_add_claimed_at():
            logger.info("Database migration for claimed_profiles.claimed_at applied successfully (or already up-to-date).")
        else:
            logger.error("Failed to apply claimed_profiles.claimed_at migration.")
            
    except Exception as e:
        logger.error(f"Error running migrations: {str(e)}") 