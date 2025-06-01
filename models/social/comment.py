"""
Comment model for handling post comments.
"""

from datetime import datetime
from extensions import db

class Comment(db.Model):
    """Model for handling post comments."""
    __tablename__ = 'comments'
    __table_args__ = {'extend_existing': True}  # Allow table to be redefined

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('comments', lazy=True))

    @classmethod
    def create(cls, post_id, user_id, content):
        """Create a new comment."""
        try:
            comment = cls(
                post_id=post_id,
                user_id=user_id,
                content=content
            )
            db.session.add(comment)
            db.session.commit()
            return comment
        except Exception as e:
            db.session.rollback()
            raise e

    @classmethod
    def get_by_id(cls, id):
        """Get a comment by ID."""
        return cls.query.get(id)

    @classmethod
    def get_by_post_id(cls, post_id):
        """Get all comments for a post."""
        return cls.query.filter_by(post_id=post_id).order_by(cls.created_at.desc()).all()

    @classmethod
    def get_by_user_id(cls, user_id):
        """Get all comments by a user."""
        return cls.query.filter_by(user_id=user_id).order_by(cls.created_at.desc()).all()

    def update(self, content):
        """Update a comment."""
        try:
            self.content = content
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def delete(self):
        """Delete a comment."""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def to_dict(self):
        """Convert the comment to a dictionary."""
        return {
            'id': self.id,
            'post_id': self.post_id,
            'user_id': self.user_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'profile_image': self.user.profile_image
            } if self.user else None
        } 