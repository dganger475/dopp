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

logger = logging.getLogger(__name__)

# Initialize database
db = SQLAlchemy()

def setup_database(app):
    """Configure database for the application"""
    
    # Configure SQLAlchemy
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': app.config.get('SQLALCHEMY_POOL_SIZE', 10),
        'pool_timeout': 30,
        'pool_recycle': 1800,
        'max_overflow': app.config.get('SQLALCHEMY_MAX_OVERFLOW', 20),
        'pool_pre_ping': True
    }
    
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Register database event listeners
    @event.listens_for(db.engine, 'connect')
    def on_connect(dbapi_connection, connection_record):
        logger.info("New database connection established")
        
        # Set pragmas for SQLite
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

@contextmanager
def db_transaction():
    """Context manager for database transactions"""
    try:
        yield db.session
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Database transaction error: {str(e)}", exc_info=True)
        raise
    finally:
        db.session.close()

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