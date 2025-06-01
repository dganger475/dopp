"""
Database Rebuild Script
=====================

This script rebuilds the database with the correct table structure and relationships.
"""

import os
import logging
from datetime import datetime
from flask import Flask
from extensions import db, init_extensions
from models.user import User
from models.social import Post, Comment, Like
from models.face import Face
from models.user_match import UserMatch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def rebuild_database():
    """Rebuild the database with correct structure."""
    try:
        # Create Flask app
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///faces.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize extensions
        init_extensions(app)
        
        # Get database path
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faces.db')
        logger.info(f"Rebuilding database at: {db_path}")
        
        # Remove existing database if it exists
        if os.path.exists(db_path):
            os.remove(db_path)
            logger.info("Removed existing database")
        
        # Create new database
        with app.app_context():
            db.create_all()
            logger.info("Created new database with tables")
            
            # Create test user
            test_user = User.create(
                username="testuser",
                email="test@example.com",
                password="password123"
            )
            if test_user:
                logger.info("Created test user")
                
                # Create test post
                test_post = Post.create(
                    user_id=test_user.id,
                    content="This is a test post"
                )
                if test_post:
                    logger.info("Created test post")
                    
                    # Create test comment
                    test_comment = Comment.create(
                        post_id=test_post.id,
                        user_id=test_user.id,
                        content="This is a test comment"
                    )
                    if test_comment:
                        logger.info("Created test comment")
                    
                    # Create test like
                    test_like = Like.create(
                        post_id=test_post.id,
                        user_id=test_user.id
                    )
                    if test_like:
                        logger.info("Created test like")
        
        logger.info("Database rebuild complete")
        return True
        
    except Exception as e:
        logger.error(f"Error rebuilding database: {e}")
        return False

if __name__ == "__main__":
    rebuild_database() 