import os
import sqlite3

DB_PATH = "faces.db"

def clean_broken_static_paths(db_path):
    if not os.path.exists(db_path):
        print("❌ Can't find the database.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Replace 'static/C:/' with 'static/extracted_faces/'
        cursor.execute("""
            UPDATE faces
            SET image_path = REPLACE(image_path, 'static/C:/', 'static/extracted_faces/')
            WHERE image_path LIKE 'static/C:/%';
        """)
        conn.commit()
        print("✅ Fixed broken 'static/C:/' paths.")
    except Exception as e:
        print(f"❌ Failed to fix: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    clean_broken_static_paths(DB_PATH)
