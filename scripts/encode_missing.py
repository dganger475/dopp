import os
import sqlite3

import face_recognition

import numpy as np

# Paths
faces_folder = r"C:\Users\1439\Documents\DopplegangerApp\static\extracted_faces"
db_path = r"C:\Users\1439\Documents\DopplegangerApp\faces.db"

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Ensure table exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE,
        encoding BLOB
    )
""")

# Get list of filenames already in database
cursor.execute("SELECT filename FROM faces")
stored_filenames = {row[0] for row in cursor.fetchall()}

# Get list of all extracted face images
extracted_filenames = set(os.listdir(faces_folder))

# Find images that are missing from the database
missing_faces = extracted_filenames - stored_filenames
print(f"🟡 Found {len(missing_faces)} missing faces that need encoding.")

# Process each missing face
for filename in missing_faces:
    image_path = os.path.join(faces_folder, filename)
    
    if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
        print(f"Skipping {filename} (not an image)")
        continue

    # Load image
    image = face_recognition.load_image_file(image_path)

    # Attempt to detect and encode face
    encodings = face_recognition.face_encodings(image)
    
    if encodings:
        encoding_blob = np.array(encodings[0], dtype=np.float32).tobytes()
        cursor.execute("INSERT INTO faces (filename, encoding) VALUES (?, ?)", (filename, encoding_blob))
        print(f"✅ Encoded and added to database: {filename}")
    else:
        print(f"❌ No face found in: {filename}")

# Commit changes and close database
conn.commit()
conn.close()

print("🎯 Encoding process completed! All missing faces have been checked.")
