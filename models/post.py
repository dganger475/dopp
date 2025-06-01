class Post(db.Model):
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    post_likes = db.relationship('Like', backref='liked_post', lazy=True)
    post_comments = db.relationship('Comment', backref='commented_post', lazy=True)
    
    def __init__(self, user_id, content, image_url=None):
        self.user_id = user_id
        self.content = content
        self.image_url = image_url
    
    def __repr__(self):
        return f'<Post {self.id}>' 