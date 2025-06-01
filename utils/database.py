"""
Database Configuration
===================

Configures database connection pooling and optimizations.
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, event
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging
import os
from dotenv import load_dotenv
import sqlite3
from flask import current_app, g
import time
from queue import Queue, Empty
import threading
from threading import Lock, Condition
from extensions import db

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize database
db = SQLAlchemy()

class DatabaseConnectionPool:
    """Database connection pool implementation."""
    
    _instance = None
    _lock = Lock()
    _condition = Condition(_lock)
    _pool = None
    _max_size = 5
    _current_size = 0
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseConnectionPool, cls).__new__(cls)
            return cls._instance
    
    def initialize(self, max_size=5):
        """Initialize the connection pool with the specified max size."""
        with self._lock:
            if self._pool is None:
                self._max_size = max_size
                self._pool = []
                logger.info(f"Initializing connection pool with max_size={max_size}")
    
    def get_connection(self):
        """Get a connection from the pool."""
        with self._lock:
            while self._current_size >= self._max_size and not self._pool:
                logger.debug("Waiting for available connection...")
                self._condition.wait()
            
            if self._pool:
                conn = self._pool.pop()
                logger.debug(f"Reusing connection from pool. Pool size: {len(self._pool)}")
                return conn
            
            self._current_size += 1
            logger.debug(f"Creating new connection. Current size: {self._current_size}")
            return self._create_connection()
    
    def return_connection(self, conn):
        """Return a connection to the pool."""
        with self._lock:
            if self._current_size > self._max_size:
                logger.debug("Closing excess connection")
                self._close_connection(conn)
                self._current_size -= 1
            else:
                logger.debug(f"Returning connection to pool. Pool size: {len(self._pool)}")
                self._pool.append(conn)
                self._condition.notify()
    
    def _create_connection(self):
        """Create a new database connection."""
        try:
            engine = create_engine(
                current_app.config['SQLALCHEMY_DATABASE_URI'],
                poolclass=QueuePool,
                pool_size=current_app.config.get('SQLALCHEMY_POOL_SIZE', 5),
                max_overflow=current_app.config.get('SQLALCHEMY_MAX_OVERFLOW', 10),
                pool_timeout=current_app.config.get('SQLALCHEMY_POOL_TIMEOUT', 30),
                pool_recycle=current_app.config.get('SQLALCHEMY_POOL_RECYCLE', 1800)
            )
            return engine.connect()
        except Exception as e:
            logger.error(f"Error creating database connection: {str(e)}")
            raise
    
    def _close_connection(self, conn):
        """Close a database connection."""
        try:
            conn.close()
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")
    
    def close_all(self):
        """Close all connections in the pool."""
        with self._lock:
            while self._pool:
                conn = self._pool.pop()
                self._close_connection(conn)
            self._current_size = 0
            logger.info("All connections closed")

# Global connection pool instance
connection_pool = DatabaseConnectionPool()

def setup_database(app):
    """Configure database for the application"""
    
    # Configure SQLAlchemy
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': app.config.get('SQLALCHEMY_POOL_SIZE', 10),
        'pool_timeout': app.config.get('SQLALCHEMY_POOL_TIMEOUT', 30),
        'pool_recycle': app.config.get('SQLALCHEMY_POOL_RECYCLE', 1800),
        'max_overflow': app.config.get('SQLALCHEMY_MAX_OVERFLOW', 20),
        'pool_pre_ping': True
    }
    
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Register database event listeners
    @event.listens_for(db.engine, 'connect')
    def on_connect(dbapi_connection, connection_record):
        logger.info("New database connection established")
        
        # Set pragmas for SQLite only
        if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.execute("PRAGMA mmap_size=30000000000")
            cursor.execute("PRAGMA cache_size=-2000")
            cursor.close()
    
    @event.listens_for(db.engine, 'checkout')
    def on_checkout(dbapi_connection, connection_record, connection_proxy):
        logger.debug("Database connection checked out from pool")
    
    @event.listens_for(db.engine, 'checkin')
    def on_checkin(dbapi_connection, connection_record):
        logger.debug("Database connection returned to pool")
    
    return db

def get_db_connection():
    """Get a database connection from the pool."""
    return db.engine.connect()

@contextmanager
def db_session():
    """Provide a transactional scope around a series of operations."""
    session = db.session
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

def init_app(app):
    """Initialize the database for the application."""
    setup_database(app)
    
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()

def get_db_stats():
    """Get database connection pool statistics"""
    stats = {
        'pool_size': db.engine.pool.size(),
        'checkedin': db.engine.pool.checkedin(),
        'overflow': db.engine.pool.overflow(),
        'checkedout': db.engine.pool.checkedout(),
    }
    return stats

def optimize_query(query):
    """Optimize a database query"""
    # Add query optimization hints
    if hasattr(query, 'execution_options'):
        query = query.execution_options(
            lazyload=False,  # Disable lazy loading
            yield_per=100    # Batch results
        )
    return query

class DatabaseError(Exception):
    """Custom exception for database errors"""
    pass

def handle_db_error(func):
    """Decorator to handle database errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Database operation failed: {str(e)}")
    return wrapper

def init_connection_pool():
    """Initialize the database connection pool."""
    max_size = current_app.config.get('SQLALCHEMY_POOL_SIZE', 5)
    connection_pool.initialize(max_size=max_size)

def close_db_connection(conn):
    """Return a database connection to the pool."""
    connection_pool.return_connection(conn)

def close_all_connections():
    """Close all database connections in the pool."""
    connection_pool.close_all() 