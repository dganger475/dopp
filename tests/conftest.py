import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

"""
Test Configuration
===============

Provides pytest fixtures and configuration for testing.
"""

import pytest
import tempfile
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime
import uuid
import shutil
import time
import logging
from sqlalchemy import inspect

from extensions import db as _db
from utils.cache import cache as _cache
from models.user import User
from routes.auth import auth as auth_blueprint

logger = logging.getLogger(__name__)

@pytest.fixture(scope='session')
def app():
    """Create and configure a Flask app for testing."""
    # Create a temporary directory for test files
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, 'test.db')
    
    # Configure the app
    app = Flask(__name__)
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'UPLOAD_FOLDER': temp_dir,
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max file size
        'SQLALCHEMY_POOL_SIZE': 5,
        'SQLALCHEMY_MAX_OVERFLOW': 10,
        'SQLALCHEMY_POOL_TIMEOUT': 30,
        'SQLALCHEMY_POOL_RECYCLE': 1800,
        'PASSWORD_MIN_LENGTH': 8,
        'PASSWORD_REQUIRE_UPPER': True,
        'PASSWORD_REQUIRE_LOWER': True,
        'PASSWORD_REQUIRE_DIGIT': True,
        'PASSWORD_REQUIRE_SPECIAL': True,
        'CACHE_TYPE': 'SimpleCache',
        'CACHE_DEFAULT_TIMEOUT': 300,
        'SESSION_TYPE': 'filesystem',
        'SESSION_FILE_DIR': temp_dir,
        'SESSION_FILE_THRESHOLD': 100,
        'SESSION_FILE_MODE': 0o600,
        'SESSION_PERMANENT': False,
        'SESSION_USE_SIGNER': True,
        'SESSION_KEY_PREFIX': 'test_session:'
    })
    
    # Initialize all extensions
    from extensions import init_extensions
    init_extensions(app)
    
    # Register blueprints
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    # Create tables
    with app.app_context():
        _db.create_all()
        print('Created tables:', inspect(_db.engine).get_table_names())  # Debug: print created tables
    
    # Push an application context
    ctx = app.app_context()
    ctx.push()
    
    yield app
    
    # Pop the application context
    ctx.pop()
    
    # Cleanup
    with app.app_context():
        _db.session.remove()
        _db.drop_all()
    
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Error removing temporary directory: {e}")

@pytest.fixture(scope='function')
def session(app):
    """Provide a session for a test and roll back after."""
    with app.app_context():
        _db.session.begin_nested()
        yield _db.session
        _db.session.rollback()
        _db.session.remove()

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def runner(app):
    """Create a test CLI runner for the app."""
    return app.test_cli_runner()

@pytest.fixture
def cache(app):
    """Get the cache instance."""
    return app.extensions['cache']

@pytest.fixture
def test_user_data():
    """Create test user data."""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'TestPass123!'
    }

@pytest.fixture
def test_user(app, session, test_user_data):
    """Create a test user."""
    with app.app_context():
        user = User(
            username=test_user_data['username'],
            email=test_user_data['email']
        )
        user.set_password(test_user_data['password'])
        session.add(user)
        session.commit()
        return user

@pytest.fixture
def auth_client(app, client, test_user):
    """Create an authenticated test client."""
    with client.session_transaction() as session:
        session['user_id'] = test_user.id
    return client

@pytest.fixture
def test_users(app, session):
    """Create test users."""
    with app.app_context():
        unique_id = str(uuid.uuid4())[:8]
        user1 = User(
            username=f"user1_{unique_id}",
            email=f"user1_{unique_id}@example.com"
        )
        user1.set_password("pass123")
        
        user2 = User(
            username=f"user2_{unique_id}",
            email=f"user2_{unique_id}@example.com"
        )
        user2.set_password("pass123")
        
        session.add_all([user1, user2])
        session.commit()
        
        yield user1, user2
        
        session.delete(user1)
        session.delete(user2)
        session.commit()

def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow to run"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test items based on command line options."""
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)

def pytest_addoption(parser):
    """Add command line options."""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration tests"
    ) 