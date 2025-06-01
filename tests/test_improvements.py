"""Test Improvements
===============

This module tests the improvements made to the application.
"""

import pytest
from flask import Flask
import sqlite3
import os
import json
from datetime import datetime

from utils.security import (
    sanitize_input, validate_email, validate_password,
    secure_headers, require_https, prevent_sql_injection,
    rate_limit_by_ip, validate_json_schema
)
from utils.monitoring import PerformanceMonitor, monitor_performance
from utils.error_handling import (
    AppError, ValidationError, AuthenticationError,
    AuthorizationError, NotFoundError, RateLimitError,
    handle_error, register_error_handlers
)
from utils.database import get_db_connection

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['DATABASE_URL'] = 'sqlite:///test.db'
    return app

@pytest.fixture
def monitor():
    """Create a performance monitor instance."""
    return PerformanceMonitor()

# Security Tests
def test_sanitize_input(app):
    """Test input sanitization."""
    with app.app_context():
        input_text = '<script>alert("xss")</script>'
        sanitized = sanitize_input(input_text)
        assert sanitized == 'alert("xss")'  # bleach removes script tags

def test_validate_email(app):
    """Test email validation."""
    with app.app_context():
        valid_email = "test@example.com"
        invalid_email = "invalid-email"
        assert sanitize_input(valid_email, is_email=True)
        assert not sanitize_input(invalid_email, is_email=True)

def test_validate_password(app):
    """Test password validation."""
    with app.app_context():
        valid_password = "StrongPass123!"
        invalid_password = "weak"
        assert sanitize_input(valid_password, is_password=True)
        assert not sanitize_input(invalid_password, is_password=True)

# Monitoring Tests
def test_record_request(app, monitor):
    """Test request recording."""
    with app.app_context():
        monitor.record_request('/test', 'GET', 200, 100)
        metrics = monitor.get_metrics()
        assert metrics['endpoints']['/test']['count'] == 1
        assert metrics['endpoints']['/test']['avg_time'] == 100

def test_record_error(app, monitor):
    """Test error recording."""
    with app.app_context():
        monitor.record_error('/test', 'GET', 'Test error', 500)
        metrics = monitor.get_metrics()
        assert metrics['errors']['/test']['count'] == 1
        assert metrics['errors']['/test']['status_codes']['500'] == 1

def test_system_metrics(app, monitor):
    """Test system metrics recording."""
    with app.app_context():
        monitor.record_system_metrics()
        metrics = monitor.get_metrics()
        assert 'cpu_usage' in metrics['system']
        assert 'memory_usage' in metrics['system']

# Error Handling Tests
def test_validation_error(app):
    """Test validation error handling."""
    with app.app_context():
        register_error_handlers(app)
        error = ValidationError("Invalid input")
        assert error.status_code == 400
        assert error.message == "Invalid input"

def test_not_found_error(app):
    """Test not found error handling."""
    with app.app_context():
        register_error_handlers(app)
        error = NotFoundError("Resource not found")
        assert error.status_code == 404
        assert error.message == "Resource not found"

def test_rate_limit_error(app):
    """Test rate limit error handling."""
    with app.app_context():
        register_error_handlers(app)
        error = RateLimitError("Too many requests")
        assert error.status_code == 429
        assert error.message == "Too many requests"

# Database Tests
def test_indexes_exist(app):
    """Test that indexes were created."""
    with app.app_context():
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check posts table indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='posts'")
        post_indexes = [row[0] for row in cursor.fetchall()]
        assert 'idx_posts_user_id' in post_indexes
        assert 'idx_posts_created_at' in post_indexes
        
        # Check comments table indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='comments'")
        comment_indexes = [row[0] for row in cursor.fetchall()]
        assert 'idx_comments_post_id' in comment_indexes
        assert 'idx_comments_user_id' in comment_indexes
        
        # Check reactions table indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='reactions'")
        reaction_indexes = [row[0] for row in cursor.fetchall()]
        assert 'idx_reactions_post_id' in reaction_indexes
        assert 'idx_reactions_user_id' in reaction_indexes
        
        conn.close()

@pytest.fixture(autouse=True)
def cleanup_test_db():
    """Clean up test database after each test."""
    yield
    if os.path.exists('test.db'):
        os.remove('test.db')

if __name__ == '__main__':
    pytest.main() 