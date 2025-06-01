"""
User Model
==========

Defines the User data model for user accounts, authentication, and profile data.
Includes relationships to faces, matches, notifications, and user utility functions.
"""

import logging
from datetime import datetime
from flask import current_app, url_for
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db
import os

# Configure logging
logger = logging.getLogger(__name__)

class User(UserMixin, db.Model):
    """User model for authentication and profile management."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    bio = db.Column(db.Text)
    hometown = db.Column(db.String(100))
    current_location_city = db.Column(db.String(100))
    current_location_state = db.Column(db.String(100))
    birthdate = db.Column(db.String(10))  # Store as string in YYYY-MM-DD format
    website = db.Column(db.String(200))
    interests = db.Column(db.Text)
    profile_image = db.Column(db.String(200))
    cover_photo = db.Column(db.String(200))
    face_filename = db.Column(db.String(200))
    profile_visibility = db.Column(db.String(20), default='public')
    share_real_name = db.Column(db.Boolean, default=False)
    share_location = db.Column(db.Boolean, default=False)
    share_age = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user_posts = db.relationship('Post', backref='post_author', lazy=True)
    user_likes = db.relationship('Like', backref='like_author', lazy=True)
    user_comments = db.relationship('Comment', backref='comment_author', lazy=True)
    followers = db.relationship(
        'User',
        secondary='follows',
        primaryjoin='User.id==follows.c.follower_id',
        secondaryjoin='User.id==follows.c.followed_id',
        backref=db.backref('following', lazy='dynamic'),
        lazy='dynamic'
    )

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if 'profile_image' not in kwargs:
            self.profile_image = current_app.config.get('DEFAULT_PROFILE_IMAGE')
        if 'cover_photo' not in kwargs:
            self.cover_photo = current_app.config.get('DEFAULT_COVER_IMAGE')

    def set_password(self, password):
        """Set the user's password hash."""
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """Verify a password against the stored hash."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self, expires_in=3600):
        """Generate a dummy auth token (for testing)."""
        import base64, os
        from datetime import datetime
        token = base64.urlsafe_b64encode(
            f"{self.id}:{datetime.utcnow().timestamp()}:{os.urandom(8).hex()}".encode()
        ).decode()
        return token

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_profile_image_url(self):
        """Return the URL for the user's profile image, checking all likely locations and falling back to a default."""
        if not self.profile_image or self.profile_image == "None":
            return url_for("static", filename="images/default_profile.png")

        if self.profile_image.startswith(("http://", "https://")):
            return self.profile_image

        # Remove any query parameters from the filename
        clean_filename = self.profile_image.split('?')[0]

        # Try profile_pics first
        profile_pics_path = os.path.join(current_app.root_path, "static", "profile_pics", clean_filename)
        if os.path.exists(profile_pics_path):
            return url_for("static", filename=f"profile_pics/{clean_filename}")

        # Try faces
        faces_path = os.path.join(current_app.root_path, "static", "faces", clean_filename)
        if os.path.exists(faces_path):
            return url_for("static", filename=f"faces/{clean_filename}")

        # Try images
        images_path = os.path.join(current_app.root_path, "static", "images", clean_filename)
        if os.path.exists(images_path):
            return url_for("static", filename=f"images/{clean_filename}")

        # Fallback to default
        return url_for("static", filename="images/default_profile.png")

    @property
    def cover_photo_url(self):
        """Return the URL for the user's cover photo."""
        if not self.cover_photo or self.cover_photo == "None" or self.cover_photo.strip() == "":
            return url_for("static", filename="images/default_cover.png")
            
        if self.cover_photo.startswith(("http://", "https://")):
            return self.cover_photo
            
        # Remove any query parameters and clean the path
        clean_path = self.cover_photo.split('?')[0]
        if clean_path.startswith('static/'):
            clean_path = clean_path[7:]  # Remove 'static/' prefix
            
        return url_for("static", filename=clean_path)

    def to_dict(self, include_private=False):
        """Convert user to dictionary, respecting privacy settings."""
        data = {
            "id": self.id,
            "username": self.username,
            "bio": self.bio,
            "profile_image": self.profile_image,
            "profile_image_url": self.get_profile_image_url(),
            "created_at": self.created_at,
            "memberSince": self.created_at,
            "hometown": self.hometown,
            "current_city": self.current_location_city,
            "current_location_state": self.current_location_state,
            "coverPhoto": self.cover_photo,
            "cover_photo": self.cover_photo,
        }

        if self.first_name or self.last_name:
            data["full_name"] = f"{self.first_name} {self.last_name}".strip()
        else:
            data["full_name"] = self.username

        if include_private or self.share_real_name:
            data["first_name"] = self.first_name
            data["last_name"] = self.last_name

        if include_private or self.share_age:
            data["birthdate"] = self.birthdate

        if include_private:
            data["email"] = self.email
            data["website"] = self.website
            data["interests"] = self.interests
            data["profile_visibility"] = self.profile_visibility

        return data

    @classmethod
    def get_by_id(cls, user_id):
        """Get a user by their ID."""
        return cls.query.get(user_id)

    @classmethod
    def get_by_username(cls, username):
        """Get a user by username."""
        return cls.query.filter_by(username=username).first()

    @classmethod
    def get_by_email(cls, email):
        """Get a user by their email."""
        return cls.query.filter_by(email=email).first()

    @classmethod
    def create(cls, username, email, password, **kwargs):
        """Create a new user."""
        if cls.query.filter_by(username=username).first() or cls.query.filter_by(email=email).first():
            return None

        user = cls(username=username, email=email, **kwargs)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    def update(self, **kwargs):
        """Update user profile information."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        db.session.commit()
        return True

    def delete(self):
        """Delete the user from the database."""
        db.session.delete(self)
        db.session.commit()
        return True

    def get_followers(self):
        """Get all followers of this user."""
        return self.followers.all()

    def get_following(self):
        """Get all users this user is following."""
        return self.following.all()

    def follow(self, user_id):
        """Follow another user."""
        if user_id == self.id:
            return False
        
        user_to_follow = User.query.get(user_id)
        if not user_to_follow:
            return False
            
        if self.is_following(user_id):
            return False
            
        self.following.append(user_to_follow)
        db.session.commit()
        return True

    def unfollow(self, user_id):
        """Unfollow another user."""
        if user_id == self.id:
            return False
            
        user_to_unfollow = User.query.get(user_id)
        if not user_to_unfollow:
            return False
            
        if not self.is_following(user_id):
            return False
            
        self.following.remove(user_to_unfollow)
        db.session.commit()
        return True

    def is_following(self, user_id):
        """Check if this user is following another user."""
        return self.following.filter_by(id=user_id).first() is not None

    def get_follower_count(self):
        """Get the number of followers this user has."""
        return self.followers.count()

    @classmethod
    def get_friend_suggestions(cls, user_id, limit=5):
        """Get friend suggestions for a user."""
        user = cls.query.get(user_id)
        if not user:
            return []
            
        # Get users who are not already followed
        following_ids = [f.id for f in user.following.all()]
        following_ids.append(user_id)  # Exclude self
        
        suggestions = cls.query.filter(
            ~cls.id.in_(following_ids)
        ).limit(limit).all()
        
        return [s.to_dict() for s in suggestions]

# Association table for follows relationship
follows = db.Table('follows',
    db.Column('follower_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('followed_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)
