"""Feed Model Tests
==============

Tests for the Feed model functionality, including:
- General feed retrieval
- User feed retrieval
- Match feed retrieval
- Trending feed retrieval
- Recommended feed retrieval
- Mentions feed retrieval
"""

import pytest
from datetime import datetime, timedelta
from models.social.feed import Feed
from models.social.post import Post
from models.user import User
from utils.db.database import get_users_db_connection

@pytest.fixture
def test_users(app):
    with app.app_context():
        user1 = User.create(
            username="user1",
            email="user1@example.com",
            password="pass123"
        )
        user2 = User.create(
            username="user2",
            email="user2@example.com",
            password="pass123"
        )
        yield user1, user2
        user1.delete()
        user2.delete()

@pytest.fixture
def test_posts(app, test_users):
    user1, user2 = test_users
    with app.app_context():
        posts = []
        # Regular posts
        for i in range(3):
            posts.append(Post.create(
                user_id=user1.id,
                content=f"User1 post {i}"
            ))
            posts.append(Post.create(
                user_id=user2.id,
                content=f"User2 post {i}"
            ))

        # Match posts
        posts.append(Post.create(
            user_id=user1.id,
            content="Match post 1",
            is_match_post=1
        ))
        posts.append(Post.create(
            user_id=user2.id,
            content="Match post 2",
            is_match_post=1
        ))

        # Posts with mentions
        posts.append(Post.create(
            user_id=user1.id,
            content=f"Post mentioning @{user2.username}"
        ))
        posts.append(Post.create(
            user_id=user2.id,
            content=f"Post mentioning @{user1.username}"
        ))
        
        yield posts
        for post in posts:
            post.delete()

def test_general_feed(app, test_users, test_posts):
    with app.app_context():
        feed = Feed.get_feed(limit=10)
        assert feed is not None
        assert len(feed) >= 8  # At least 8 posts (3 regular + 1 match + 1 mention from each user)

def test_user_feed(app, test_users, test_posts):
    user1, _ = test_users
    with app.app_context():
        feed = Feed.get_user_feed(user1.id, limit=10)
        assert feed is not None
        assert len(feed) >= 5  # At least 5 posts (3 regular + 1 match + 1 mention)

def test_match_feed(app, test_users, test_posts):
    user1, _ = test_users
    with app.app_context():
        feed = Feed.get_match_feed(user1.id, limit=10)
        assert feed is not None
        assert len(feed) >= 2  # At least 2 match posts

def test_trending_feed(app, test_users, test_posts):
    with app.app_context():
        feed = Feed.get_trending_feed(limit=10)
        assert feed is not None
        assert isinstance(feed, list)

def test_recommended_feed(app, test_users, test_posts):
    user1, _ = test_users
    with app.app_context():
        feed = Feed.get_recommended_feed(user1.id, limit=10)
        assert feed is not None
        assert isinstance(feed, list)

def test_mentions_feed(app, test_users, test_posts):
    user1, _ = test_users
    with app.app_context():
        feed = Feed.get_mentions_feed(user1.id, limit=10)
        assert feed is not None
        assert len(feed) >= 1  # At least 1 mention

def test_feed_pagination(app, test_users, test_posts):
    with app.app_context():
        # Get first page
        feed1 = Feed.get_feed(limit=5, offset=0)
        assert feed1 is not None
        assert len(feed1) <= 5

        # Get second page
        feed2 = Feed.get_feed(limit=5, offset=5)
        assert feed2 is not None
        assert len(feed2) <= 5

        # Verify no overlap
        feed1_ids = {post['id'] for post in feed1}
        feed2_ids = {post['id'] for post in feed2}
        assert len(feed1_ids.intersection(feed2_ids)) == 0

def test_feed_ordering(app, test_users, test_posts):
    with app.app_context():
        feed = Feed.get_feed(limit=10)
        assert feed is not None
        
        # Verify posts are ordered by created_at in descending order
        for i in range(len(feed) - 1):
            current_post = datetime.strptime(feed[i]['created_at'], "%Y-%m-%d %H:%M:%S")
            next_post = datetime.strptime(feed[i + 1]['created_at'], "%Y-%m-%d %H:%M:%S")
            assert current_post >= next_post

if __name__ == '__main__':
    pytest.main() 