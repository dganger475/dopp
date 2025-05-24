import os
import sqlite3

DATABASE_FILE = r"C:\Users\1439\Documents\DopplegangerApp\faces.db"
EXTRACTED_FOLDER = r"C:\Users\1439\Documents\DopplegangerApp\static\extracted_faces"

def find_orphaned_entries():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Fetch all image paths from the database
    cursor.execute("SELECT image_path FROM faces")
    db_images = [row[0] for row in cursor.fetchall()]

    # Find images that do not exist on disk
    missing_images = [img for img in db_images if not os.path.exists(img)]
    
    conn.close()

    print(f"🔹 Orphaned Entries Found: {len(missing_images)}")
    for img in missing_images[:10]:  # Print only the first 10 for review
        print(f"⚠️ Missing File: {img}")

    return missing_images

missing_images = find_orphaned_entries()
