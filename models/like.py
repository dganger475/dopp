from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Like(db.Model):
    __tablename__ = 'likes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    post = db.relationship('Post', backref='post_likes', lazy=True)
    
    def __init__(self, user_id, post_id):
        self.user_id = user_id
        self.post_id = post_id
    
    def __repr__(self):
        return f'<Like {self.id}>' 