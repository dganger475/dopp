import os
import re
import sqlite3
from multiprocessing import Pool, cpu_count

import face_recognition
from tqdm import tqdm

import numpy as np

FACES_DIR = r"C:\Users\1439\Documents\DopplegangerApp\static\extracted_faces"
DB_PATH = r"C:\Users\1439\Documents\DopplegangerApp\faces.db"
APP_ROOT = r"C:\Users\1439\Documents\DopplegangerApp"
NUM_WORKERS = max(cpu_count() - 1, 1)

def parse_filename(filename):
    name = os.path.splitext(os.path.basename(filename))[0]
    year_match = re.search(r'\b(19|20)\d{2}\b', name)
    page_match = re.search(r'[_\-]p(?:age)?[_\-]?(\d+)', name, re.IGNORECASE)
    face_match = re.search(r'[_\-]f(?:ace)?[_\-]?(\d+)', name, re.IGNORECASE)

    year = year_match.group(0) if year_match else "Unknown"
    page = int(page_match.group(1)) if page_match else None
    face = int(face_match.group(1)) if face_match else None

    parts = re.split(r'[_\-]', name)
    school_parts = [p for p in parts if not re.search(r'^\d{4}$|page|face|p\d+|f\d+', p, re.IGNORECASE)]
    school = " ".join(school_parts).strip() or "Unknown"
    return year, school, page, face

def get_already_encoded():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
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
    rows = conn.execute("SELECT filename FROM faces").fetchall()
    conn.close()
    return set(r[0] for r in rows)

def process_image(path):
    try:
        image = face_recognition.load_image_file(path)
        encodings = face_recognition.face_encodings(image)
        if not encodings:
            return None
        encoding = np.array(encodings[0], dtype=np.float64)
        filename = os.path.basename(path)
        year, school, page, face = parse_filename(filename)
        rel_path = os.path.relpath(path, APP_ROOT).replace("\\", "/")
        return (
            filename,
            rel_path,
            encoding.tobytes(),
            year,
            school,
            page,
            face
        )
    except Exception as e:
        print(f"⚠️ Error processing {path}: {e}")
        return None

def insert_batch(entries):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    inserted = 0
    for entry in entries:
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO faces (
                    filename, image_path, encoding,
                    year, school_name, page_number, face_number
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, entry)
            inserted += 1
        except Exception as e:
            print(f"❌ Failed to insert {entry[0]}: {e}")
    conn.commit()
    conn.close()
    print(f"✅ Inserted into DB: {inserted}")

def encode_all():
    all_images = [
        os.path.join(dp, f)
        for dp, dn, filenames in os.walk(FACES_DIR)
        for f in filenames if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ]
    already = get_already_encoded()
    images_to_encode = [f for f in all_images if os.path.basename(f) not in already]

    print(f"🔍 Total: {len(all_images)} | Skipping {len(already)} already in DB")
    print(f"⚡ Encoding {len(images_to_encode)} new faces using {NUM_WORKERS} workers...")

    with Pool(NUM_WORKERS) as pool:
        results = list(tqdm(pool.imap(process_image, images_to_encode), total=len(images_to_encode)))

    results = [r for r in results if r]
    insert_batch(results)

    print(f"\n✅ Encoded: {len(results)}")
    print(f"❌ Skipped: {len(images_to_encode) - len(results)}")

if __name__ == "__main__":
    encode_all()
