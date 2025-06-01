"""Script to delete a specific test post from the database"""

from utils.db.database import get_users_db_connection

def delete_specific_post():
    """Delete a specific test post from December 1969"""
    try:
        conn = get_users_db_connection()
        cursor = conn.cursor()
        
        # First, let's find the post with content 'Test post'
        cursor.execute("SELECT id, user_id, content, created_at FROM posts WHERE content = 'Test post'")
        posts = cursor.fetchall()
        
        if not posts:
            print("No posts found with content 'Test post'")
            
            # Let's try to find any posts from December 1969
            cursor.execute("SELECT id, user_id, content, created_at FROM posts WHERE created_at LIKE '%1969%'")
            posts = cursor.fetchall()
            
            if not posts:
                print("No posts found from December 1969")
                
                # Let's list all posts
                cursor.execute("SELECT id, user_id, content, created_at FROM posts")
                posts = cursor.fetchall()
                
                if not posts:
                    print("No posts found in the database")
                    return
        
        # Display all found posts
        print(f"Found {len(posts)} posts:")
        for post in posts:
            post_id, user_id, content, created_at = post
            print(f"ID: {post_id}, User ID: {user_id}, Content: {content}, Created: {created_at}")
        
        # Ask which post to delete
        post_id = input("Enter the ID of the post to delete (or 'all' to delete all listed posts): ")
        
        if post_id.lower() == 'all':
            for post in posts:
                post_id = post[0]
                cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
                print(f"Deleted post with ID {post_id}")
            conn.commit()
            print("All listed posts deleted successfully")
        else:
            try:
                post_id = int(post_id)
                cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
                if cursor.rowcount > 0:
                    conn.commit()
                    print(f"Post with ID {post_id} deleted successfully")
                else:
                    print(f"No post found with ID {post_id}")
            except ValueError:
                print("Invalid post ID. Please enter a valid number.")
        
        conn.close()
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    delete_specific_post()
