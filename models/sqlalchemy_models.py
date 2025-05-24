"""
SQLAlchemy models for database migrations.

These models mirror the existing SQLite schema but use SQLAlchemy ORM,
allowing us to use Flask-Migrate for database migrations.
"""

"""
SQLAlchemy Base Models
=====================

Contains SQLAlchemy ORM base models and database configuration for the DoppleGänger app.
"""
from datetime import datetime

from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.sql import func
from sqlalchemy import Index

# Import the shared SQLAlchemy instance from extensions
from extensions import db


class User(db.Model):
    """User model for authentication and profile management."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    hometown = db.Column(db.String(100), nullable=True)
    # Changed to reflect target schema: city and state instead of single current_location
    current_location_city = db.Column(db.String(100), nullable=True)
    current_location_state = db.Column(db.String(50), nullable=True)
    birthdate = db.Column(db.Date, nullable=True)
    website = db.Column(db.String(100), nullable=True)
    interests = db.Column(db.Text, nullable=True)
    profile_image = db.Column(db.String(255), nullable=True)
    cover_photo = db.Column(db.String(255), nullable=True)
    profile_visibility = db.Column(db.String(20), default="public")
    share_real_name = db.Column(db.Boolean, default=False)
    share_location = db.Column(db.Boolean, default=False)
    share_age = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    # Temporarily commented out for focused migration
    # matches = db.relationship("Match", backref="user", lazy=True)
    # notifications = db.relationship("Notification", backref="user", lazy=True)
    posts_authored = db.relationship("Post", backref="author", lazy="dynamic", foreign_keys='Post.user_id')

    # Relationships for UserSavedMatch and FeedPost
    saved_matches_made = db.relationship('UserSavedMatch', foreign_keys='UserSavedMatch.user_id', backref='saver', lazy='dynamic')
    profiles_saved_by_others = db.relationship('UserSavedMatch', foreign_keys='UserSavedMatch.matched_user_id', backref='saved_profile', lazy='dynamic')
    authored_feed_posts = db.relationship('FeedPost', foreign_keys='FeedPost.user_id', backref='author_feed_post', lazy='dynamic') # author_feed_post to avoid conflict
    shared_in_feed_posts = db.relationship('FeedPost', foreign_keys='FeedPost.shared_profile_id', backref='shared_user_profile_feed_post', lazy='dynamic') # shared_user_profile_feed_post to avoid conflict

    def set_password(self, password):
        """Set the password hash from a plaintext password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_posts_user_id_users'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to User (author) handled by User.posts_authored backref
    # Temporarily commented out for focused migration
    # reactions = db.relationship("Reaction", backref="post", lazy="dynamic")

    def __repr__(self):
        return f'<Post {self.id} by User {self.user_id}>'


class Face(db.Model):
    """Face model for storing face data and metadata."""

    __tablename__ = "faces"

    id = db.Column(db.Integer, primary_key=True)
    # filename unique constraint defined in __table_args__ for explicit naming
    filename = db.Column(db.String(255), nullable=False)
    encoding = db.Column(db.LargeBinary, nullable=True)  # Face encoding as binary blob
    yearbook_year = db.Column(db.Integer, nullable=True)
    school_name = db.Column(db.String(255), nullable=True)
    page_number = db.Column(db.Integer, nullable=True)
    face_box = db.Column(
        db.String(255), nullable=True
    )  # JSON string of face bounding box
    state = db.Column(db.String(50), nullable=True)
    decade = db.Column(db.String(10), nullable=True)
    quality_score = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    # Temporarily commented out for focused migration
    # matches = db.relationship("Match", backref="face", lazy=True)

    # Explicitly named unique constraint to match migration 95006cc80290
    __table_args__ = (db.UniqueConstraint('filename', name='uix_faces_filename'),)

    def __repr__(self):
        return f"<Face {self.filename}>"


class Match(db.Model):
    """Match model for storing user-face matches."""

    __tablename__ = "matches"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    face_id = db.Column(db.Integer, db.ForeignKey("faces.id"), nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)
    is_claimed = db.Column(db.Boolean, default=False)
    is_favorite = db.Column(db.Boolean, default=False)
    is_visible = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Match {self.id}>"


class Notification(db.Model):
    """Notification model for user notifications."""

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type = db.Column(
        db.String(50), nullable=False
    )  # e.g., 'match_claimed', 'new_comment'
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    related_id = db.Column(
        db.Integer, nullable=True
    )  # ID of related object (match, comment, etc.)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notification {self.id}>"


class Reaction(db.Model):
    __tablename__ = "reactions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    reaction_type = db.Column(db.String(32), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "post_id", name="uix_user_post"),)

    def __repr__(self):
        return f"<Reaction {self.id} by User {self.user_id} on Post {self.post_id}>"


class UserSavedMatch(db.Model):
    __tablename__ = 'user_saved_matches'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_user_saved_matches_user_id_users'), nullable=False)
    matched_user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_user_saved_matches_matched_user_id_users'), nullable=False)
    # Optionally, if you want to link to a specific face that triggered the match:
    # matched_face_id = db.Column(db.Integer, db.ForeignKey('faces.id', name='fk_user_saved_matches_matched_face_id_faces'), nullable=True)
    saved_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    # Explicitly named indexes
    __table_args__ = (
        Index('ix_user_saved_matches_user_id', 'user_id'),
        Index('ix_user_saved_matches_matched_user_id', 'matched_user_id'),
    )

    # Example relationships (uncomment and adjust if needed):
    saver = db.relationship('User', foreign_keys=[user_id], backref=db.backref('saved_matches_made_backref', lazy='dynamic'))
    saved_profile = db.relationship('User', foreign_keys=[matched_user_id], backref=db.backref('profiles_saved_by_others_backref', lazy='dynamic'))

    def __repr__(self):
        return f'<UserSavedMatch {self.user_id} saved {self.matched_user_id}>'


class FeedPost(db.Model):
    __tablename__ = 'feed_posts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_feed_posts_user_id_users'), nullable=False)
    post_type = db.Column(db.String(50), nullable=False, default='shared_match') # e.g., 'shared_match', 'status_update', 'new_match_found'
    
    # For shared matches/profiles
    shared_profile_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_feed_posts_shared_profile_id_users'), nullable=True)
    # Optionally, if sharing a specific face match:
    # shared_face_id = db.Column(db.Integer, db.ForeignKey('faces.id', name='fk_feed_posts_shared_face_id_faces'), nullable=True)

    content_text = db.Column(db.Text, nullable=True) # Optional text accompanying the share or post
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    
    # Explicitly named indexes
    __table_args__ = (
        Index('ix_feed_posts_user_id', 'user_id'),
        Index('ix_feed_posts_shared_profile_id', 'shared_profile_id'),
    )

    # Example relationships (uncomment and adjust if needed):
    author = db.relationship('User', foreign_keys=[user_id], backref=db.backref('authored_feed_posts_backref', lazy='dynamic'))
    shared_user_profile = db.relationship('User', foreign_keys=[shared_profile_id], backref=db.backref('shared_in_feed_posts_backref', lazy='dynamic'))

    def __repr__(self):
        return f'<FeedPost {self.id} by {self.user_id} of type {self.post_type}>'
