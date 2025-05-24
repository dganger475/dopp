import os
import sqlite3

# 🔥 Update this to your real database path
DB_PATH = 'faces.db'

# Connect to the database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Find all broken entries: image_path is NULL
cursor.execute("SELECT id, filename FROM faces WHERE image_path IS NULL;")
broken_entries = cursor.fetchall()

print(f"\n🔎 Found {len(broken_entries)} broken entries to fix...\n")

for entry in broken_entries:
    entry_id, broken_filename = entry
    
    # Only fix if filename contains a path
    if '/' in broken_filename or '\\' in broken_filename:
        # Extract the real filename only
        real_filename = os.path.basename(broken_filename)
        
        # Construct the correct image_path
        correct_image_path = os.path.join('static', 'extracted_faces', real_filename).replace("\\", "/")
        
        # Update the row
        cursor.execute("""
            UPDATE faces
            SET filename = ?, image_path = ?
            WHERE id = ?
        """, (real_filename, correct_image_path, entry_id))
        
        print(f"✅ Fixed ID {entry_id}: filename -> '{real_filename}', image_path -> '{correct_image_path}'")

# Save and close
conn.commit()
conn.close()

print("\n🎯 All broken entries fixed successfully!")
