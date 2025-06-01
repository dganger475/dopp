"""Integration Tests
==============

This module contains integration tests to verify the entire system works together.
"""

import pytest
from flask import Flask
from models.user import User
from models.post import Post
from models.social.comment import Comment
from models.social.like import Like
from models.social.reaction import Reaction
from models.notification import Notification
from models.user_match import UserMatch
from utils.database import get_db_connection
from utils.security import sanitize_input, prevent_sql_injection
from utils.monitoring import PerformanceMonitor
from utils.error_handling import ValidationError, NotFoundError, RateLimitError
import os
import threading
import time

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['DATABASE_URL'] = 'sqlite:///test.db'
    app.config['DEFAULT_PROFILE_IMAGE'] = 'default.jpg'
    return app

@pytest.fixture
def test_db(app):
    """Initialize test database."""
    with app.app_context():
        conn = get_db_connection()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                profile_image TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                reaction_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        conn.commit()
        conn.close()
        yield
        conn = get_db_connection()
        conn.execute("DELETE FROM notifications")
        conn.execute("DELETE FROM reactions")
        conn.execute("DELETE FROM comments")
        conn.execute("DELETE FROM posts")
        conn.execute("DELETE FROM users")
        conn.commit()
        conn.close()
        if os.path.exists('test.db'):
            os.remove('test.db')

@pytest.fixture
def test_users(app, test_db):
    """Create test users."""
    with app.app_context():
        user1 = User.create(
            username="testuser1",
            email="test1@example.com",
            password="testpass123"
        )
        user2 = User.create(
            username="testuser2",
            email="test2@example.com",
            password="testpass123"
        )
        yield user1, user2

@pytest.fixture
def monitor(app):
    """Create a performance monitor instance."""
    with app.app_context():
        return PerformanceMonitor()

def test_post_creation_and_interaction(app, test_users):
    """Test post creation and interaction flow."""
    user1, user2 = test_users
    with app.app_context():
        # Create a post
        post = Post.create(
            user_id=user1.id,
            content="Test post content"
        )
        assert post is not None
        
        # Add a comment
        comment = Comment.create(
            post_id=post.id,
            user_id=user2.id,
            content="Test comment"
        )
        assert comment is not None
        
        # Add a reaction
        reaction = Reaction.create(
            post_id=post.id,
            user_id=user2.id,
            reaction_type="like"
        )
        assert reaction is not None
        
        # Verify interactions
        post_comments = Comment.get_by_post_id(post.id)
        assert len(post_comments) == 1
        
        post_reactions = Reaction.get_by_post_id(post.id)
        assert len(post_reactions) == 1

def test_notification_flow(app, test_users):
    """Test notification system flow."""
    user1, user2 = test_users
    with app.app_context():
        # Create a post
        post = Post.create(
            user_id=user1.id,
            content="Test post content"
        )
        
        # Add a comment to trigger notification
        comment = Comment.create(
            post_id=post.id,
            user_id=user2.id,
            content="Test comment"
        )
        
        # Check notification
        notifications = Notification.get_by_user_id(user1.id)
        assert len(notifications) == 1
        assert notifications[0].type == "comment"
        
        # Mark as read
        Notification.mark_as_read(notifications[0].id)
        updated_notification = Notification.get_by_id(notifications[0].id)
        assert updated_notification.is_read

def test_concurrent_operations(app, test_users):
    """Test concurrent operations."""
    user1, _ = test_users
    with app.app_context():
        def create_post(user_id):
            with app.app_context():
                Post.create(
                    user_id=user_id,
                    content=f"Test post from user {user_id}"
                )
        
        # Create multiple posts concurrently
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_post, args=(user1.id,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify posts were created
        posts = Post.get_by_user_id(user1.id)
        assert len(posts) == 5

def test_error_handling_flow(app, test_users):
    """Test error handling flow."""
    user1, _ = test_users
    with app.app_context():
        # Test validation error
        with pytest.raises(ValidationError):
            Post.create(
                user_id=user1.id,
                content=""  # Empty content should raise validation error
            )
        
        # Test not found error
        with pytest.raises(NotFoundError):
            Post.get_by_id(999)  # Non-existent post ID
        
        # Test rate limit error
        for _ in range(100):  # Exceed rate limit
            sanitize_input("test")
        with pytest.raises(RateLimitError):
            sanitize_input("test")

def test_performance_monitoring(app, monitor):
    """Test performance monitoring integration."""
    with app.app_context():
        # Record some requests
        monitor.record_request('/test', 'GET', 200, 100)
        monitor.record_request('/test', 'GET', 200, 200)
        
        # Record an error
        monitor.record_error('/test', 'GET', 'Test error')
        
        # Get metrics
        metrics = monitor.get_metrics()
        assert metrics['endpoints']['/test']['count'] == 2
        assert metrics['endpoints']['/test']['avg_time'] == 150
        assert metrics['errors']['/test:GET']['count'] == 1

def test_security_integration(app):
    """Test security features integration."""
    with app.app_context():
        # Test XSS prevention
        input_text = '<script>alert("xss")</script>'
        sanitized = sanitize_input(input_text)
        assert sanitized == 'alert("xss")'
        
        # Test SQL injection prevention
        malicious_input = "'; DROP TABLE users; --"
        sanitized = prevent_sql_injection(malicious_input)
        assert "DROP TABLE" not in sanitized

if __name__ == '__main__':
    pytest.main() 