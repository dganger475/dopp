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
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from config import get_settings
from sqlalchemy.pool import QueuePool
import urllib.parse
from sqlalchemy.exc import SQLAlchemyError

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

settings = get_settings()

# Create SQLAlchemy engine
engine = create_engine(settings.DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

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

def get_users_db_connection(db_path=None, app=None):
    """
    Compatibility function for legacy code that expects get_users_db_connection.
    This function now uses SQLAlchemy to maintain compatibility with the new database system.
    
    Args:
        db_path: Ignored in new system, kept for compatibility
        app: Optional Flask app instance. If not provided, tries to use current_app.
    
    Returns:
        A SQLAlchemy session object that can be used like the old connection.
    """
    try:
        if current_app:
            return current_app.db.session
        else:
            # Create a new engine and session if not in app context
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                raise ValueError("DATABASE_URL environment variable is not set")
            
            # Parse the URL to ensure it's properly encoded
            parsed = urllib.parse.urlparse(db_url)
            encoded_password = urllib.parse.quote(parsed.password)
            db_url = db_url.replace(parsed.password, encoded_password)
            
            # Configure the engine with Supabase-specific settings
            engine = create_engine(
                db_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                connect_args={
                    'connect_timeout': 10,
                    'application_name': 'dopple_app',
                    'options': '-c statement_timeout=30000'  # 30 second timeout
                }
            )
            
            # Test the connection
            try:
                with engine.connect() as conn:
                    conn.execute("SELECT 1")
            except SQLAlchemyError as e:
                logging.error(f"Failed to connect to Supabase: {e}")
                raise
            
            Session = sessionmaker(bind=engine)
            return Session()
    except Exception as e:
        logging.error(f"Error getting database connection: {str(e)}")
        raise

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

def get_db_connection():
    """Get a database connection using SQLAlchemy."""
    try:
        if current_app:
            return current_app.db.session
        else:
            # Create a new engine and session if not in app context
            engine = create_engine(
                os.getenv('DATABASE_URL'),
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800
            )
            Session = sessionmaker(bind=engine)
            return Session()
    except Exception as e:
        logger.error(f"Error getting database connection: {str(e)}")
        raise

def get_db_engine():
    """Get the SQLAlchemy engine instance."""
    try:
        if current_app:
            return current_app.db.engine
        else:
            return create_engine(
                os.getenv('DATABASE_URL'),
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800
            )
    except Exception as e:
        logger.error(f"Error getting database engine: {str(e)}")
        raise

def execute_query(query, params=None):
    """Execute a SQL query using SQLAlchemy."""
    try:
        session = get_db_connection()
        result = session.execute(query, params or {})
        session.commit()
        return result
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

def execute_many(query, params_list):
    """Execute multiple SQL queries using SQLAlchemy."""
    try:
        session = get_db_connection()
        for params in params_list:
            session.execute(query, params or {})
        session.commit()
    except Exception as e:
        logger.error(f"Error executing multiple queries: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

def get_table_names():
    """Get list of all table names in the database."""
    try:
        engine = get_db_engine()
        return engine.table_names()
    except Exception as e:
        logger.error(f"Error getting table names: {str(e)}")
        raise

def get_table_schema(table_name):
    """Get schema information for a specific table."""
    try:
        engine = get_db_engine()
        return engine.dialect.get_columns(engine, table_name)
    except Exception as e:
        logger.error(f"Error getting table schema: {str(e)}")
        raise

def get_db() -> Session:
    """
    Get a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# For backward compatibility
def get_users_db_connection():
    """
    Legacy function for backward compatibility.
    Returns a database session.
    """
    return SessionLocal()

def setup_users_db():
    """
    Initialize the users database and create necessary tables.
    This function is called during application startup.
    """
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logging.info("Successfully initialized users database")
    except Exception as e:
        logging.error(f"Error initializing users database: {e}")
        raise
