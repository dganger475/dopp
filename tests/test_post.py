"""Post Model Tests
==============

Tests for the Post model functionality, including:
- Post creation and retrieval
- Feed operations
- User interactions
- Data validation
"""

import pytest
from datetime import datetime
from models.post import Post
from models.user import User
from utils.database import get_db_connection
import os
from tests.conftest import app

@pytest.fixture
def test_post(app, test_user):
    with app.app_context():
        post = Post.create(user_id=test_user.id, content="Test post content")
        yield post
        post.delete()


def test_post_creation(app, test_user):
    with app.app_context():
        post = Post.create(user_id=test_user.id, content="Test post content")
        assert post is not None
        assert post.user_id == test_user.id
        assert post.content == "Test post content"
        assert isinstance(post.created_at, datetime)
        post.delete()


def test_post_retrieval(app, test_user):
    with app.app_context():
        post = Post.create(user_id=test_user.id, content="Test post content")
        retrieved_post = Post.get_by_id(post.id)
        assert retrieved_post is not None
        assert retrieved_post.id == post.id
        assert retrieved_post.user_id == post.user_id
        assert retrieved_post.content == post.content
        post.delete()


def test_post_update(app, test_user):
    with app.app_context():
        post = Post.create(user_id=test_user.id, content="Test post content")
        new_content = "Updated post content"
        updated_post = post.update(new_content)
        assert updated_post.content == new_content
        # Verify update in database
        retrieved_post = Post.get_by_id(post.id)
        assert retrieved_post.content == new_content
        post.delete()


def test_post_deletion(app, test_user):
    with app.app_context():
        post = Post.create(user_id=test_user.id, content="Test post content")
        post_id = post.id
        post.delete()
        # Verify deletion
        deleted_post = Post.get_by_id(post_id)
        assert deleted_post is None


def test_post_pagination(app, test_user):
    with app.app_context():
        posts = []
        for i in range(25):
            post = Post.create(user_id=test_user.id, content=f"Test post {i}")
            posts.append(post)
        # Test first page
        first_page = Post.get_by_user_id(test_user.id, page=1, per_page=10)
        assert len(first_page) == 10
        # Test second page
        second_page = Post.get_by_user_id(test_user.id, page=2, per_page=10)
        assert len(second_page) == 10
        # Test third page
        third_page = Post.get_by_user_id(test_user.id, page=3, per_page=10)
        assert len(third_page) == 5
        # Clean up
        for post in posts:
            post.delete()

if __name__ == '__main__':
    pytest.main() 