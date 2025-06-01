import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_posts_table():
    try:
        conn = sqlite3.connect('faces.db')
        cursor = conn.cursor()

        # 1. Create new table with updated_at column
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts_new (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        logger.info('Created posts_new table.')

        # 2. Copy data from old posts table, set updated_at = created_at
        cursor.execute('''
            INSERT INTO posts_new (id, user_id, content, created_at, updated_at)
            SELECT id, user_id, content, created_at, created_at FROM posts
        ''')
        logger.info('Copied data from posts to posts_new.')

        # 3. Drop old posts table
        cursor.execute('DROP TABLE posts')
        logger.info('Dropped old posts table.')

        # 4. Rename new table to posts
        cursor.execute('ALTER TABLE posts_new RENAME TO posts')
        logger.info('Renamed posts_new to posts.')

        conn.commit()
        logger.info('Migration completed successfully!')
        return True
    except Exception as e:
        logger.error(f'Error during migration: {e}')
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    success = migrate_posts_table()
    exit(0 if success else 1) 