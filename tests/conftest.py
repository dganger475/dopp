"""
Test Configuration
===============

Provides pytest fixtures and configuration for testing.
"""

import os
import pytest
import tempfile
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from config import TestingConfig
from utils.database import db as _db
from utils.cache import cache as _cache
from models.user import User

@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    app = Flask(__name__)
    app.config.from_object(TestingConfig)
    
    # Create temp directory for test files
    test_dir = tempfile.mkdtemp()
    app.config['UPLOAD_FOLDER'] = os.path.join(test_dir, 'uploads')
    app.config['PROFILE_PICS_FOLDER'] = os.path.join(test_dir, 'profile_pics')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROFILE_PICS_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    _db.init_app(app)
    _cache.init_app(app)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create tables
    with app.app_context():
        _db.create_all()
    
    return app

@pytest.fixture(scope='session')
def db(app):
    """Create database for the tests."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()

@pytest.fixture(scope='session')
def cache(app):
    """Create cache for the tests."""
    return _cache

@pytest.fixture(scope='function')
def session(db):
    """Create a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()
    
    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)
    
    db.session = session
    
    yield session
    
    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()

@pytest.fixture
def auth_client(app, client):
    """Create an authenticated test client."""
    with app.app_context():
        user = User(
            username='test_user',
            email='test@example.com'
        )
        user.set_password('password123')
        _db.session.add(user)
        _db.session.commit()
        
        client.post('/login', json={
            'username': 'test_user',
            'password': 'password123'
        })
        
        yield client
        
        _db.session.delete(user)
        _db.session.commit()

@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User(
        username='test_user',
        email='test@example.com'
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    
    yield user
    
    db.session.delete(user)
    db.session.commit()

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
    """Modify test collection."""
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
    
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)

def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="run slow tests"
    )
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration tests"
    ) 