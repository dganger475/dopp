import sqlite3
import logging
import os

# Assuming your project structure allows this import:
# If utils.db.database is not found, you might need to adjust the Python path
# or temporarily copy get_users_db_connection or its logic here.
try:
    from utils.db.database import get_users_db_connection, DATABASE_CONFIG
except ImportError:
    print("Error: Could not import get_users_db_connection from utils.db.database.")
    print("Please ensure your PYTHONPATH is set up correctly or run this script from the project root.")
    # Fallback or simplified connection logic if direct import fails
    # This assumes dev.db is in a 'data/db' subdirectory relative to where this script is run
    # or relative to a known project root. Adjust if necessary.
    
    # Determine Project Root (heuristic)
    # Assuming the script is in the project root, or one level down in a 'scripts' folder
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(PROJECT_ROOT) == 'scripts':
        PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)

    DB_NAME_FALLBACK = 'faces.db' # Corrected database name for fallback
    DB_PATH_FALLBACK = os.path.join(PROJECT_ROOT, DB_NAME_FALLBACK) # Corrected path for fallback
    
    DATABASE_CONFIG = {'users_db': DB_PATH_FALLBACK } # Simplified config

    def get_users_db_connection():
        db_path = DATABASE_CONFIG.get('users_db')
        if not db_path:
            logging.error("Users database path not configured.")
            return None
        
        # Ensure the directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir)
                logging.info(f"Created database directory: {db_dir}")
            except OSError as e:
                logging.error(f"Error creating database directory {db_dir}: {e}")
                return None

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        logging.info(f"Connected to users database: {db_path}")
        return conn
    
    print(f"Using fallback database connection logic. DB path: {DATABASE_CONFIG.get('users_db')}")


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

FACE_LIKES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS face_likes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    face_id INTEGER NOT NULL,
    liked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (face_id) REFERENCES faces (id) ON DELETE CASCADE,
    UNIQUE (user_id, face_id)
);
"""

FACE_LIKES_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_face_likes_user_id ON face_likes (user_id);",
    "CREATE INDEX IF NOT EXISTS idx_face_likes_face_id ON face_likes (face_id);"
]

def create_tables():
    conn = None
    try:
        conn = get_users_db_connection()
        if conn is None:
            logger.error("Failed to get database connection. Cannot create tables.")
            return

        cursor = conn.cursor()
        
        logger.info("Attempting to create 'face_likes' table...")
        cursor.execute(FACE_LIKES_TABLE_SQL)
        logger.info("'face_likes' table creation statement executed.")
        
        for index_sql in FACE_LIKES_INDEXES_SQL:
            logger.info(f"Attempting to create index: {index_sql.split('ON')[0].split('EXISTS')[-1].strip()}...")
            cursor.execute(index_sql)
            logger.info(f"Index creation statement executed: {index_sql.split('ON')[0].split('EXISTS')[-1].strip()}")
            
        conn.commit()
        logger.info("Successfully created 'face_likes' table and its indexes (if they didn't exist).")

    except sqlite3.Error as e:
        logger.error(f"SQLite error occurred: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    logger.info("Starting script to create 'face_likes' table...")
    create_tables()
    logger.info("Script finished.")
