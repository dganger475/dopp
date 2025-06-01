import os
import re
import sqlite3

# CONFIGURATION
FACES_DIR = os.path.join(os.getcwd(), "static", "extracted_faces")
DB_PATH = os.path.join(os.getcwd(), "faces.db")  # Change if your DB is elsewhere

# Regex for allowed characters (alphanumeric, dash, underscore, dot)
safe_char_re = re.compile(r'[^A-Za-z0-9._-]')

# Connect to the database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Track changes for reporting
changes = []

for filename in os.listdir(FACES_DIR):
    old_path = os.path.join(FACES_DIR, filename)
    if not os.path.isfile(old_path):
        continue

    # Create a safe filename
    new_filename = filename.replace(' ', '_').replace('%', '_')
    new_filename = safe_char_re.sub('_', new_filename)
    new_path = os.path.join(FACES_DIR, new_filename)

    if old_path != new_path:
        print(f"Renaming: {filename} -> {new_filename}")
        os.rename(old_path, new_path)
        # Update the database
        cursor.execute(
            "UPDATE faces SET filename = ? WHERE filename = ?",
            (new_filename, filename)
        )
        changes.append((filename, new_filename))

# Commit DB changes
conn.commit()
conn.close()

print(f"\nDone! Renamed {len(changes)} files and updated the database.")
if changes:
    print("Summary of changes:")
    for old, new in changes:
        print(f"  {old} -> {new}")
else:
    print("No files needed renaming.") 