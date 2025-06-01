"""Script to delete test posts from the database"""

from utils.db.database import get_users_db_connection
from models.post import Post

def delete_test_posts():
    """Delete test posts from the database"""
    try:
        # Get all posts
        posts = Post.get_all()
        print(f"Found {len(posts)} posts in the database")
        
        # Print post details
        for post in posts:
            print(f"Post ID: {post.id}, Content: {post.content[:30]}..., User ID: {post.user_id}")
            
        # Ask for confirmation to delete specific post
        post_id = input("Enter the ID of the post to delete (or 'all' to delete all posts): ")
        
        if post_id.lower() == 'all':
            # Delete all posts
            conn = get_users_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM posts")
            conn.commit()
            conn.close()
            print("All posts deleted successfully")
        else:
            # Delete specific post
            try:
                post_id = int(post_id)
                post = Post.get_by_id(post_id)
                if post:
                    post.delete()
                    print(f"Post with ID {post_id} deleted successfully")
                else:
                    print(f"No post found with ID {post_id}")
            except ValueError:
                print("Invalid post ID. Please enter a valid number.")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    delete_test_posts()
