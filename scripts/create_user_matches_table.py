import sqlite3

DB_PATH = 'faces.db'  # Path to your main database file

def create_user_matches_table():
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                match_filename TEXT NOT NULL,
                similarity REAL,
                is_favorite BOOLEAN DEFAULT 0,
                is_visible BOOLEAN DEFAULT 1,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        conn.commit()
        print('user_matches table created or already exists.')
    finally:
        conn.close()

if __name__ == '__main__':
    create_user_matches_table()
