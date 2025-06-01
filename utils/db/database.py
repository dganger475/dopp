import logging
import sqlite3
import os
from flask import current_app, g
from contextlib import contextmanager
import atexit
import threading
import time
from sqlite3 import OperationalError
from typing import Optional, Generator, List
from queue import Queue
from threading import Lock

"""
Database Utilities
=================

Provides helper functions for database access, queries, and migrations.
"""

# Default path if not using app config - consolidated to one DB
DEFAULT_DB_PATH = "faces.db"

# Global connection pool with thread safety
_connection_pool = {}
_connection_lock = threading.Lock()
_connection_last_used = {}

# Add these constants at the top of the file
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
CONNECTION_TIMEOUT = 30  # seconds

def _cleanup_connections():
    """Clean up all database connections when the application exits."""
    with _connection_lock:
        for conn in _connection_pool.values():
            try:
                conn.close()
            except Exception as e:
                logging.error(f"Error closing database connection during cleanup: {e}")
        _connection_pool.clear()
        _connection_last_used.clear()

atexit.register(_cleanup_connections)

def _validate_connection(conn, db_path):
    """Validate if a connection is still alive and usable."""
    try:
        # Try a simple query
        conn.execute("SELECT 1")
        return True
    except sqlite3.Error:
        return False

def _get_connection_from_pool(db_path):
    """Get a connection from the pool with retries."""
    with _connection_lock:
        # Try to get an existing connection from the pool
        if db_path in _connection_pool:
            conn = _connection_pool[db_path]
            if _validate_connection(conn, db_path):
                # Remove from pool since we're using it
                del _connection_pool[db_path]
                return conn
            else:
                # Connection is invalid, remove it
                try:
                    conn.close()
                except Exception as e:
                    logging.error(f"Error closing invalid connection: {e}")
                del _connection_pool[db_path]

    # If we get here, we need to create a new connection
    for attempt in range(MAX_RETRIES):
        try:
            conn = sqlite3.connect(db_path, timeout=CONNECTION_TIMEOUT)
            conn.row_factory = sqlite3.Row
            return conn
        except OperationalError as e:
            if attempt < MAX_RETRIES - 1:
                logging.warning(f"Database connection attempt {attempt + 1} failed: {e}. Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logging.error(f"Failed to connect to database after {MAX_RETRIES} attempts: {e}")
                raise
        except Exception as e:
            logging.error(f"Unexpected error connecting to database: {e}")
            raise

@contextmanager
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
    conn = None
    try:
        if db_path is None:
            effective_app = app or current_app
            if effective_app:
                db_path = effective_app.config.get("DB_PATH", DEFAULT_DB_PATH)
            else:
                db_path = DEFAULT_DB_PATH

        # Ensure the directory for the db_path exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir)
                logging.info(f"Created directory for database: {db_dir}")
            except OSError as e:
                logging.error(f"Failed to create directory {db_dir}: {e}")
                return None

        # Create a new connection with check_same_thread=False to allow cross-thread usage
        conn = sqlite3.connect(db_path, timeout=CONNECTION_TIMEOUT, check_same_thread=False)
        conn.row_factory = sqlite3.Row

        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        yield conn
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        raise
    finally:
        if conn:
            try:
                conn.close()
            except Exception as e:
                logging.error(f"Error closing database connection: {e}")

def close_all_connections():
    """Close all database connections in the pool."""
    with _connection_lock:
        for conn in _connection_pool.values():
            try:
                conn.close()
            except Exception as e:
                logging.error(f"Error closing database connection: {e}")
        _connection_pool.clear()
        _connection_last_used.clear()

def get_users_db_connection():
    """Get a connection to the users database."""
    try:
        conn = sqlite3.connect('faces.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logging.error(f"Error connecting to users database: {e}")
        return None

def close_db(e=None):
    """Close the database connection stored in g object."""
    db = g.pop("db", None)
    if db is not None:
        try:
            db.close()
        except Exception as e:
            logging.error(f"Error closing db connection: {e}")

    users_db = g.pop("users_db", None)
    if users_db is not None:
        try:
            users_db.close()
        except Exception as e:
            logging.error(f"Error closing users_db connection: {e}")

def init_app(app):
    """Initialize database connection for the application."""
    # Ensure the database directory exists
    db_path = app.config.get("DB_PATH", DEFAULT_DB_PATH)
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir)
            logging.info(f"Created directory for database: {db_dir}")
        except OSError as e:
            logging.error(f"Failed to create directory {db_dir}: {e}")
            return

    # Create database if it doesn't exist
    if not os.path.exists(db_path):
        try:
            with get_db_connection(db_path) as conn:
                # Create tables
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS faces (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        embedding BLOB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS claimed_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        face_id INTEGER NOT NULL,
                        relationship TEXT,
                        caption TEXT,
                        claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        FOREIGN KEY (face_id) REFERENCES faces(id)
                    )
                """)
                conn.commit()
                logging.info("Database tables created successfully")
        except Exception as e:
            logging.error(f"Error creating database tables: {e}")
            return

def setup_users_db(app=None):
    """
    Initialize the users database tables if they don't exist.

    Args:
        app: Optional Flask app instance.
    """
    try:
        with get_db_connection(app=app) as conn:
            cursor = conn.cursor()

            # Create users table
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                face_id INTEGER NOT NULL,
                relationship TEXT,
                caption TEXT,
                claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (face_id) REFERENCES faces(id)
            )
            """
            )

            # Add missing columns if they don't exist
            cursor.execute("PRAGMA table_info(claimed_profiles)")
            columns = [col[1] for col in cursor.fetchall()]

            if 'relationship' not in columns:
                cursor.execute("ALTER TABLE claimed_profiles ADD COLUMN relationship TEXT")
                logging.info("Added relationship column to claimed_profiles table")

            if 'caption' not in columns:
                cursor.execute("ALTER TABLE claimed_profiles ADD COLUMN caption TEXT")
                logging.info("Added caption column to claimed_profiles table")

            if 'status' not in columns:
                cursor.execute("ALTER TABLE claimed_profiles ADD COLUMN status TEXT DEFAULT 'pending'")
                logging.info("Added status column to claimed_profiles table")

            if 'face_id' not in columns:
                cursor.execute("ALTER TABLE claimed_profiles ADD COLUMN face_id INTEGER REFERENCES faces(id)")
                logging.info("Added face_id column to claimed_profiles table")

            if 'claimed_at' not in columns:
                cursor.execute("ALTER TABLE claimed_profiles ADD COLUMN claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                logging.info("Added claimed_at column to claimed_profiles table")

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
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                following_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(follower_id, following_id),
                FOREIGN KEY (follower_id) REFERENCES users(id),
                FOREIGN KEY (following_id) REFERENCES users(id)
            )
            """
            )

            conn.commit()
            logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error setting up users database: {e}")
        raise

class DatabaseConnectionPool:
    """A thread-safe connection pool for database connections."""
    
    def __init__(self, max_connections=10):
        self.max_connections = max_connections
        self.connections = Queue(maxsize=max_connections)
        self.lock = Lock()
        self.initialize()
    
    def initialize(self):
        """Initialize the connection pool."""
        for _ in range(self.max_connections):
            try:
                conn = sqlite3.connect('faces.db')
                conn.row_factory = sqlite3.Row
                self.connections.put(conn)
            except Exception as e:
                logging.error(f"Error initializing connection pool: {e}")
    
    def size(self):
        """Get the current size of the connection pool."""
        return self.connections.qsize()
    
    def get_connection(self):
        """Get a connection from the pool."""
        try:
            conn = self.connections.get(timeout=5)
            if not self._validate_connection(conn):
                conn.close()
                conn = sqlite3.connect('faces.db')
                conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logging.error(f"Error getting connection from pool: {e}")
            return None
    
    def release_connection(self, conn):
        """Release a connection back to the pool."""
        try:
            if self._validate_connection(conn):
                self.connections.put(conn)
            else:
                conn.close()
        except Exception as e:
            logging.error(f"Error releasing connection to pool: {e}")
    
    def _validate_connection(self, conn):
        """Validate if a connection is still alive."""
        try:
            conn.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    def close_all(self):
        """Close all connections in the pool."""
        while not self.connections.empty():
            try:
                conn = self.connections.get()
                conn.close()
            except Exception as e:
                logging.error(f"Error closing connection: {e}")

@contextmanager
def get_db_connection():
    """Get a database connection from the pool."""
    conn = None
    try:
        conn = _get_connection_from_pool('faces.db')
        yield conn
    finally:
        if conn:
            with _connection_lock:
                _connection_pool['faces.db'] = conn
                _connection_last_used['faces.db'] = time.time()

def init_db():
    """Initialize the database with required tables."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create faces table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS faces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE NOT NULL,
                    image_path TEXT NOT NULL,
                    encoding BLOB,
                    yearbook_year TEXT,
                    school_name TEXT,
                    page_number INTEGER,
                    decade TEXT,
                    state TEXT,
                    claimed_by_user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (claimed_by_user_id) REFERENCES users(id) ON DELETE SET NULL
                )
            """)
            
            # Create claimed profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS claimed_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    face_id INTEGER NOT NULL,
                    relationship TEXT,
                    caption TEXT,
                    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (face_id) REFERENCES faces(id)
                )
            """)
            
            # Create posts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    is_match_post INTEGER DEFAULT 0,
                    face_filename TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Create comments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY,
                    post_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (post_id) REFERENCES posts(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Create likes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS likes (
                    id INTEGER PRIMARY KEY,
                    post_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(post_id, user_id),
                    FOREIGN KEY (post_id) REFERENCES posts(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Create follows table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS follows (
                    id INTEGER PRIMARY KEY,
                    follower_id INTEGER NOT NULL,
                    following_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(follower_id, following_id),
                    FOREIGN KEY (follower_id) REFERENCES users(id),
                    FOREIGN KEY (following_id) REFERENCES users(id)
                )
            """)
            
            conn.commit()
            logging.info("Database tables created successfully")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        raise

def close_db(e=None):
    """Close the database connection stored in g object."""
    db = g.pop("db", None)
    if db is not None:
        try:
            db.close()
        except Exception as e:
            logging.error(f"Error closing db connection: {e}")

    users_db = g.pop("users_db", None)
    if users_db is not None:
        try:
            users_db.close()
        except Exception as e:
            logging.error(f"Error closing users_db connection: {e}")

def close_users_db(conn):
    """Close a users database connection."""
    if conn is not None:
        try:
            conn.close()
        except Exception as e:
            logging.error(f"Error closing users database connection: {e}")
