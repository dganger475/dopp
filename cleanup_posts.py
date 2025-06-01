import sqlite3
import re
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection():
    """Get a connection to the SQLite database."""
    db_path = os.path.join(os.getcwd(), 'faces.db')
    logging.info(f"Connecting to database at {db_path}")
    return sqlite3.connect(db_path)

def clean_post_content():
    """Clean post content to remove filenames and standardize match posts."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Get all match posts
        cursor.execute("SELECT id, content, is_match_post, face_filename FROM posts WHERE is_match_post = 1")
        match_posts = cursor.fetchall()
        
        logging.info(f"Found {len(match_posts)} match posts to clean")
        
        for post_id, content, is_match_post, face_filename in match_posts:
            # Extract similarity from content if possible
            similarity_match = re.search(r'(\d+)%', content)
            similarity = similarity_match.group(1) if similarity_match else "unknown"
            
            # Create clean content
            clean_content = f"I found my historical doppelganger with {similarity}% similarity!"
            
            # Update the post content
            cursor.execute(
                "UPDATE posts SET content = ? WHERE id = ?",
                (clean_content, post_id)
            )
            
            logging.info(f"Cleaned post {post_id}: {clean_content}")
            
            # If face_filename is null but there's a filename in the content, extract and update it
            if not face_filename:
                # Try to extract filename from content
                filename_match = re.search(r'#([\w_]+\.jpg)', content)
                if filename_match:
                    extracted_filename = filename_match.group(1)
                    cursor.execute(
                        "UPDATE posts SET face_filename = ? WHERE id = ?",
                        (extracted_filename, post_id)
                    )
                    logging.info(f"Updated face_filename for post {post_id}: {extracted_filename}")
        
        conn.commit()
        logging.info("All match posts have been cleaned successfully")
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Error cleaning posts: {e}")
    finally:
        conn.close()

def main():
    """Main function to run the cleanup."""
    logging.info("Starting post cleanup process")
    clean_post_content()
    logging.info("Post cleanup process completed")

if __name__ == "__main__":
    main()
