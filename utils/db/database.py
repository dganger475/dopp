import logging
from flask import current_app
from extensions import db
from contextlib import contextmanager
import atexit
import threading
import time
from typing import Optional, Generator, List
from queue import Queue
from threading import Lock

"""
Database Utilities
=================

Provides helper functions for database access, queries, and migrations.
"""

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

def _validate_connection(conn):
    """Validate if a connection is still alive and usable."""
    try:
        # Try a simple query
        conn.execute("SELECT 1")
        return True
    except Exception as e:
        logging.error(f"Connection validation failed: {e}")
        return False

def _get_connection_from_pool():
    """Get a connection from the pool with retries."""
    with _connection_lock:
        # Try to get an existing connection from the pool
        if 'default' in _connection_pool:
            conn = _connection_pool['default']
            if _validate_connection(conn):
                # Remove from pool since we're using it
                del _connection_pool['default']
                return conn
            else:
                # Connection is invalid, remove it
                try:
                    conn.close()
                except Exception as e:
                    logging.error(f"Error closing invalid connection: {e}")
                del _connection_pool['default']

    # If we get here, we need to create a new connection
    for attempt in range(MAX_RETRIES):
        try:
            # Get the database URL from the app config
            db_url = current_app.config['SQLALCHEMY_DATABASE_URI']
            logging.info(f"Attempting to connect to database with URL: {db_url}")
            
            # Create a new connection
            conn = db.engine.connect()
            logging.info("Successfully connected to database")
            return conn
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                logging.warning(f"Database connection attempt {attempt + 1} failed: {e}. Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logging.error(f"Failed to connect to database after {MAX_RETRIES} attempts: {e}")
                raise

@contextmanager
def get_db_connection():
    """
    Get a database connection using SQLAlchemy.
    This function serves as the primary way to get a connection.

    Returns:
        A SQLAlchemy connection object or None if connection fails.
    """
    conn = None
    try:
        conn = _get_connection_from_pool()
        try:
            yield conn
            # If no exception occurred, commit the transaction
            conn.commit()
        except Exception as e:
            # If an exception occurred, rollback the transaction
            conn.rollback()
            raise
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        raise
    finally:
        if conn:
            try:
                # Ensure any remaining transaction is rolled back
                try:
                    conn.rollback()
                except Exception:
                    pass  # Ignore errors during rollback
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

def close_db(e=None):
    """Close the database connection stored in g object."""
    db = g.pop("db", None)
    if db is not None:
        try:
            db.close()
        except Exception as e:
            logging.error(f"Error closing db connection: {e}")

def init_app(app):
    """Initialize database connection for the application."""
    # Initialize SQLAlchemy with PostgreSQL-specific settings
    db.init_app(app)
    
    # Create tables if they don't exist
    with app.app_context():
        try:
            db.create_all()
            logging.info("Successfully created/verified database tables")
        except Exception as e:
            logging.error(f"Error creating database tables: {e}")
            raise
    
    return app
