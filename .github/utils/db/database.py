import logging
import sqlite3
import os

"""
Database Utilities
=================

Provides helper functions for database access, queries, and migrations.
"""
from flask import current_app, g

# Default path if not using app config - consolidated to one DB
DEFAULT_DB_PATH = "faces.db"


def get_db_connection(db_path=None, app=None):
    """
    Get a database connection to the main application database (faces.db).
    This function now serves as the primary way to get a connection, 
    as users and faces tables are consolidated.

    Args:
        db_path: Optional path to the database. If not provided, uses the app config.
        app: Optional Flask app instance. If not provided, tries to use current_app.

    Returns:
        A SQLite connection object or None if connection fails.
    """
    if db_path is None:
        effective_app = app or current_app
        if effective_app:
            # Use DB_PATH which now points to faces.db (containing all tables)
            db_path = effective_app.config.get("DB_PATH", DEFAULT_DB_PATH)
        else:
            # Outside of application context, use default path
            db_path = DEFAULT_DB_PATH

    try:
        # Ensure the directory for the db_path exists, especially if it's in an instance folder
        # For simple filenames, this might not be strictly necessary but good practice for robustness
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir)
                logging.info(f"Created directory for database: {db_dir}")
            except OSError as e:
                logging.error(f"Failed to create directory {db_dir}: {e}")
                # Potentially return None or raise error if directory creation is critical

        conn = sqlite3.connect(db_path, timeout=20, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        return None


def get_users_db_connection(db_path=None, app=None):
    """
    Get a database connection to the main application database (faces.db).
    This function is now an alias or wrapper for get_db_connection,
    as user data is in the same database file.

    Args:
        db_path: Optional path to the database. If not provided, uses the app config.
        app: Optional Flask app instance. If not provided, tries to use current_app.

    Returns:
        A SQLite connection object or None if connection fails.
    """
    # All data is now in the database pointed to by DB_PATH (faces.db)
    # So this function behaves identically to get_db_connection
    initial_db_path_arg = db_path
    effective_app = app or current_app
    
    logging.info(f"[DB_UTIL] get_users_db_connection called. current_app is {'SET' if effective_app else 'NOT SET'}. Passed db_path: {initial_db_path_arg}")

    if db_path is None:
        if effective_app:
            db_path_from_config = effective_app.config.get("DB_PATH")
            logging.info(f"[DB_UTIL] Using current_app.config['DB_PATH']: {db_path_from_config}")
            db_path = db_path_from_config or DEFAULT_DB_PATH # Fallback if DB_PATH is None in config
        else:
            logging.info(f"[DB_UTIL] current_app is None, using DEFAULT_DB_PATH: {DEFAULT_DB_PATH}")
            db_path = DEFAULT_DB_PATH
            
    logging.info(f"[DB_UTIL] get_users_db_connection attempting to connect to (resolved path): {os.path.abspath(db_path)}")
    logging.info(f"[DB_UTIL] Current Working Directory: {os.getcwd()}")

    try:
        conn = sqlite3.connect(db_path, timeout=20)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logging.error(f"Users database connection failed: {e}")
        return None


def close_db(e=None):
    """Close the database connection stored in g object."""
    db = g.pop("db", None)
    if db is not None:
        db.close()

    users_db = g.pop("users_db", None)
    if users_db is not None:
        users_db.close()


def init_app(app):
    """Register database functions with the Flask app."""
    app.teardown_appcontext(close_db)


def setup_users_db(app=None):
    """
    Initialize the users database tables if they don't exist.

    Args:
        app: Optional Flask app instance.
    """
    conn = get_db_connection(app=app)
    if not conn:
        logging.error("Failed to connect to users database for setup")
        return False

    cursor = conn.cursor()

    # Create users table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        first_name TEXT,
        last_name TEXT,
        bio TEXT,
        hometown TEXT,
        current_location_city TEXT,
        current_location_state TEXT,
        birthdate TEXT,
        website TEXT,
        interests TEXT,
        profile_image TEXT,
        face_encoding BLOB,
        cover_photo TEXT,
        profile_visibility TEXT DEFAULT 'public',
        share_real_name INTEGER DEFAULT 0,
        share_location INTEGER DEFAULT 0,
        share_age INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )

    # Create faces table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE NOT NULL,
        image_path TEXT NOT NULL,
        encoding BLOB,
        yearbook_year TEXT,       -- Store as TEXT for flexibility (e.g., '1990s' or 'Unknown')
        school_name TEXT,
        page_number INTEGER,
        decade TEXT,              -- Explicit decade (e.g., '1980s')
        state TEXT,               -- State associated with the image (e.g., from yearbook)
        claimed_by_user_id INTEGER, -- User who has claimed this face as their own profile
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (claimed_by_user_id) REFERENCES users(id) ON DELETE SET NULL
    )
    """
    )

    # Create claimed profiles table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS claimed_profiles (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        face_filename TEXT UNIQUE NOT NULL,
        relationship TEXT,
        caption TEXT,
        claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """
    )

    # Create posts table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        is_match_post INTEGER DEFAULT 0,
        face_filename TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """
    )

    # Create comments table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (post_id) REFERENCES posts(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """
    )

    # Create likes table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY,
        post_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(post_id, user_id),
        FOREIGN KEY (post_id) REFERENCES posts(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """
    )

    # Create follows table for user relationships
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS follows (
        id INTEGER PRIMARY KEY,
        follower_id INTEGER NOT NULL,
        followed_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(follower_id, followed_id),
        FOREIGN KEY (follower_id) REFERENCES users(id),
        FOREIGN KEY (followed_id) REFERENCES users(id)
    )
    """
    )

    # Create user_matches table for tracking which matches to show on profile
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS user_matches (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        match_filename TEXT NOT NULL,
        is_visible INTEGER DEFAULT 1,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, match_filename),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """
    )

    conn.commit()
    conn.close()

    return True
