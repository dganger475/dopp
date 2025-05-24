import os
import sqlite3

import face_recognition

import numpy as np

TEST_IMG = r"C:\Users\1439\Documents\DopplegangerApp\static\extracted_faces\2005 Holmes Community College_2005_p14_face1 - Copy.jpg"
DB_PATH = r"C:\Users\1439\Documents\DopplegangerApp\faces.db"

def parse_filename(filename):
    name = os.path.splitext(os.path.basename(filename))[0]
    return "2025", "Test School", 1, 1  # fallback

image = face_recognition.load_image_file(TEST_IMG)
encodings = face_recognition.face_encodings(image)
if not encodings:
    print("❌ No face found")
    exit()

encoding = np.array(encodings[0], dtype=np.float64)
filename = os.path.basename(TEST_IMG)
year, school, page, face = parse_filename(filename)

rel_path = os.path.relpath(TEST_IMG, r"C:\Users\1439\Documents\DopplegangerApp").replace("\\", "/")

entry = (
    filename,
    rel_path,
    encoding.tobytes(),
    year,
    school,
    page,
    face
)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE,
        image_path TEXT,
        encoding BLOB,
        year TEXT,
        school_name TEXT,
        page_number INTEGER,
        face_number INTEGER
    )
""")
cursor.execute("INSERT OR REPLACE INTO faces (filename, image_path, encoding, year, school_name, page_number, face_number) VALUES (?, ?, ?, ?, ?, ?, ?)", entry)
conn.commit()
conn.close()

print("✅ Inserted test face successfully with correct relative path!")
