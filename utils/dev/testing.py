"""
Testing Utilities
==============

Provides utilities for testing and mock data generation.
"""

import random
import string
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any

def generate_random_string(length: int = 10) -> str:
    """Generate a random string of fixed length."""
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def generate_random_email() -> str:
    """Generate a random email address."""
    domains = ['example.com', 'test.com', 'mock.org', 'fake.net']
    username = generate_random_string(8)
    domain = random.choice(domains)
    return f"{username}@{domain}"

def generate_random_date(
    start_date: datetime = None,
    end_date: datetime = None
) -> datetime:
    """Generate a random date between start_date and end_date."""
    if not start_date:
        start_date = datetime.now() - timedelta(days=365)
    if not end_date:
        end_date = datetime.now()
    
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return start_date + timedelta(days=random_days)

class MockDataGenerator:
    """Generate mock data for testing."""
    
    @staticmethod
    def user(
        id: int = None,
        username: str = None,
        email: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate mock user data."""
        return {
            'id': id or random.randint(1, 10000),
            'username': username or generate_random_string(),
            'email': email or generate_random_email(),
            'created_at': datetime.now().isoformat(),
            'profile_image': f"/static/profile_pics/user_{generate_random_string(6)}.jpg",
            **kwargs
        }
    
    @staticmethod
    def users(count: int = 5) -> List[Dict[str, Any]]:
        """Generate multiple mock users."""
        return [MockDataGenerator.user() for _ in range(count)]
    
    @staticmethod
    def post(
        user_id: int = None,
        id: int = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate mock post data."""
        return {
            'id': id or random.randint(1, 10000),
            'user_id': user_id or random.randint(1, 10000),
            'content': f"Mock post content {generate_random_string(20)}",
            'created_at': datetime.now().isoformat(),
            'likes_count': random.randint(0, 100),
            'comments_count': random.randint(0, 50),
            **kwargs
        }
    
    @staticmethod
    def posts(count: int = 5, user_id: int = None) -> List[Dict[str, Any]]:
        """Generate multiple mock posts."""
        return [MockDataGenerator.post(user_id=user_id) for _ in range(count)]
    
    @staticmethod
    def comment(
        post_id: int = None,
        user_id: int = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate mock comment data."""
        return {
            'id': random.randint(1, 10000),
            'post_id': post_id or random.randint(1, 10000),
            'user_id': user_id or random.randint(1, 10000),
            'content': f"Mock comment {generate_random_string(10)}",
            'created_at': datetime.now().isoformat(),
            **kwargs
        }
    
    @staticmethod
    def comments(
        count: int = 5,
        post_id: int = None,
        user_id: int = None
    ) -> List[Dict[str, Any]]:
        """Generate multiple mock comments."""
        return [
            MockDataGenerator.comment(post_id=post_id, user_id=user_id)
            for _ in range(count)
        ]

def create_test_data(db) -> Dict[str, Any]:
    """Create a set of test data in the database."""
    from models.user import User
    from models.social.post import Post
    from models.comment import Comment
    
    # Create test users
    users = []
    for i in range(3):
        user = User(
            username=f"test_user_{i}",
            email=f"test{i}@example.com"
        )
        user.set_password("password123")
        db.session.add(user)
        users.append(user)
    
    # Create test posts
    posts = []
    for user in users:
        for _ in range(2):
            post = Post(
                user_id=user.id,
                content=f"Test post by {user.username}"
            )
            db.session.add(post)
            posts.append(post)
    
    # Create test comments
    comments = []
    for post in posts:
        for user in random.sample(users, 2):
            comment = Comment(
                post_id=post.id,
                user_id=user.id,
                content=f"Test comment by {user.username}"
            )
            db.session.add(comment)
            comments.append(comment)
    
    db.session.commit()
    
    return {
        'users': users,
        'posts': posts,
        'comments': comments
    } 