"""Interaction Model Tests
====================

Tests for the Interaction model functionality, including:
- Comments
- Likes
- Reactions
- Shares
"""

import pytest
from datetime import datetime
from models.social.interaction import Comment, Like, Reaction, Share
from models.social.post import Post
from models.user import User
from utils.db.database import get_users_db_connection

@pytest.fixture
def test_post(app, test_user):
    with app.app_context():
        post = Post.create(user_id=test_user.id, content="Test post content")
        yield post
        post.delete()


def test_comment_creation(app, test_user, test_post):
    with app.app_context():
        comment = Comment.create(post_id=test_post.id, user_id=test_user.id, content="Test comment")
        assert comment is not None
        assert comment.post_id == test_post.id
        assert comment.user_id == test_user.id
        assert comment.content == "Test comment"
        comment.delete()


def test_comment_retrieval(app, test_user, test_post):
    with app.app_context():
        comment = Comment.create(post_id=test_post.id, user_id=test_user.id, content="Test comment")
        retrieved_comment = Comment.get_by_id(comment.id)
        assert retrieved_comment is not None
        assert retrieved_comment.id == comment.id
        assert retrieved_comment.post_id == comment.post_id
        assert retrieved_comment.user_id == comment.user_id
        assert retrieved_comment.content == comment.content
        comment.delete()


def test_post_comments(app, test_user, test_post):
    with app.app_context():
        comment = Comment.create(post_id=test_post.id, user_id=test_user.id, content="Test comment")
        comments = Comment.get_by_post_id(test_post.id)
        assert len(comments) == 1
        assert comments[0].id == comment.id
        comment.delete()


def test_like_creation(app, test_user, test_post):
    with app.app_context():
        like = Like.create(post_id=test_post.id, user_id=test_user.id)
        assert like is not None
        assert like.post_id == test_post.id
        assert like.user_id == test_user.id
        like.delete()


def test_like_retrieval(app, test_user, test_post):
    with app.app_context():
        like = Like.create(post_id=test_post.id, user_id=test_user.id)
        retrieved_like = Like.get_by_id(like.id)
        assert retrieved_like is not None
        assert retrieved_like.id == like.id
        assert retrieved_like.post_id == like.post_id
        assert retrieved_like.user_id == like.user_id
        like.delete()


def test_like_count(app, test_user, test_post):
    with app.app_context():
        like = Like.create(post_id=test_post.id, user_id=test_user.id)
        count = Like.get_like_count(test_post.id)
        assert count == 1
        like.delete()


def test_reaction_creation(app, test_user, test_post):
    with app.app_context():
        reaction = Reaction.create(post_id=test_post.id, user_id=test_user.id, reaction_type="like")
        assert reaction is not None
        assert reaction.post_id == test_post.id
        assert reaction.user_id == test_user.id
        assert reaction.reaction_type == "like"
        reaction.delete()


def test_reaction_update(app, test_user, test_post):
    with app.app_context():
        reaction = Reaction.create(post_id=test_post.id, user_id=test_user.id, reaction_type="like")
        updated_reaction = reaction.update("love")
        assert updated_reaction.reaction_type == "love"
        reaction.delete()


def test_reaction_count(app, test_user, test_post):
    with app.app_context():
        reaction = Reaction.create(post_id=test_post.id, user_id=test_user.id, reaction_type="like")
        count = Reaction.get_reaction_count(test_post.id)
        assert count == 1
        reaction.delete()


def test_share_creation(app, test_user, test_post):
    with app.app_context():
        share = Share.create(post_id=test_post.id, user_id=test_user.id)
        assert share is not None
        assert share.post_id == test_post.id
        assert share.user_id == test_user.id
        share.delete()


def test_share_count(app, test_user, test_post):
    with app.app_context():
        share = Share.create(post_id=test_post.id, user_id=test_user.id)
        count = Share.get_share_count(test_post.id)
        assert count == 1
        share.delete()

if __name__ == '__main__':
    pytest.main() 