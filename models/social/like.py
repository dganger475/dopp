"""
Like model for handling post likes.
"""

from datetime import datetime
from extensions import db

class Like(db.Model):
    """Model for post likes."""
    __tablename__ = 'likes'
    __table_args__ = {'extend_existing': True}  # Allow table to be redefined

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('likes', lazy=True, cascade='all, delete-orphan'))
    post = db.relationship('Post', backref=db.backref('post_likes', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<Like {self.id}>'

    @classmethod
    def create(cls, post_id: int, user_id: int) -> 'Like':
        """Create a new like."""
        try:
            like = cls(
                post_id=post_id,
                user_id=user_id
            )
            db.session.add(like)
            db.session.commit()
            return like
        except Exception as e:
            db.session.rollback()
            raise e

    @classmethod
    def get_by_id(cls, like_id: int) -> 'Like':
        """Get a like by ID."""
        return cls.query.get(like_id)

    @classmethod
    def get_by_post_id(cls, post_id: int) -> list['Like']:
        """Get all likes for a post."""
        return cls.query.filter_by(post_id=post_id).order_by(cls.created_at.desc()).all()

    @classmethod
    def get_by_user_id(cls, user_id: int) -> list['Like']:
        """Get all likes by a user."""
        return cls.query.filter_by(user_id=user_id).order_by(cls.created_at.desc()).all()

    @classmethod
    def get_like_count(cls, post_id: int) -> int:
        """Get the number of likes for a post."""
        return cls.query.filter_by(post_id=post_id).count()

    def delete(self) -> None:
        """Delete a like."""
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

    def to_dict(self) -> dict:
        """Convert the like to a dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'post_id': self.post_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 