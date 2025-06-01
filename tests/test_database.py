"""Database Connection Tests
======================

Tests for database connection management, including:
- Connection pool initialization
- Connection retrieval and return
- Error handling
- Timeout handling
"""

import pytest
import time
from utils.database import connection_pool, get_db_connection, close_db_connection

@pytest.fixture
def pool():
    """Create a fresh connection pool for testing."""
    connection_pool.close_all()
    connection_pool.initialize()
    yield connection_pool
    connection_pool.close_all()

def test_connection_pool_initialization(pool):
    """Test connection pool initialization."""
    assert pool.initialized
    assert pool.size() == pool.max_size

def test_connection_retrieval(pool):
    """Test connection retrieval from the pool."""
    conn = get_db_connection()
    assert conn is not None
    assert pool.size() == pool.max_size
    close_db_connection()

def test_connection_reuse(pool):
    """Test connection reuse from the pool."""
    conn1 = get_db_connection()
    close_db_connection()
    conn2 = get_db_connection()
    assert conn1 is conn2
    close_db_connection()

def test_connection_timeout(pool):
    """Test connection timeout handling."""
    # Get all available connections
    connections = []
    for _ in range(pool.max_size):
        conn = get_db_connection()
        connections.append(conn)
    
    # Try to get one more connection (should timeout)
    start_time = time.time()
    with pytest.raises(TimeoutError):
        get_db_connection()
    assert time.time() - start_time >= pool.timeout
    
    # Return connections to pool
    for conn in connections:
        close_db_connection()

def test_connection_error_handling(pool):
    """Test connection error handling."""
    # Force an error by closing the pool
    pool.close_all()
    
    # Try to get a connection (should raise an error)
    with pytest.raises(Exception):
        get_db_connection()
    
    # Reinitialize pool
    pool.initialize()

def test_connection_validation(pool):
    """Test connection validation."""
    conn = get_db_connection()
    assert pool._validate_connection(conn)
    close_db_connection()

if __name__ == '__main__':
    pytest.main() 