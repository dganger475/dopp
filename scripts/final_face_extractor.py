import multiprocessing
import os
import pickle
import re
import sqlite3
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime

import face_recognition
import fitz
from PIL import Image

import numpy as np

# -------- CONFIG --------
PDF_FOLDER = r"C:\Users\1439\Documents\DopplegangerApp\downloads"
OUTPUT_FOLDER = r"static\extracted_faces"
DB_PATH = "faces.db"
TARGET_SIZE = (300, 300)
# ------------------------

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def extract_year_from_filename(name):
    match = re.search(r"(19|20)\d{2}", name)
    return match.group() if match else "Unknown"

def get_extracted_date():
    return datetime.now().strftime("%Y-%m-%d")

def get_school_and_location(filename):
    parts = filename.replace("_", " ").replace("-", " ").split()
    school_name = " ".join(parts[1:3]) if len(parts) > 2 else "Unknown School"
    location = "Unknown Location"
    return school_name, location

def is_collage(face_locations, threshold=0.12):
    for i, (top1, right1, bottom1, left1) in enumerate(face_locations):
        for j, (top2, right2, bottom2, left2) in enumerate(face_locations):
            if i != j:
                dist = np.sqrt((left1 - left2) ** 2 + (top1 - top2) ** 2)
                if dist < threshold * TARGET_SIZE[0]:
                    return True
    return False

def check_face_quality(face_image):
    # Check image size
    if face_image.size < (100, 100):
        return False
        
    # Check brightness
    brightness = np.mean(face_image)
    if brightness < 30 or brightness > 220:
        return False
        
    # Check contrast
    contrast = np.std(face_image)
    if contrast < 20:
        return False
        
    return True

def process_page(args):
    pdf_path, page_number = args
    results = []

    try:
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        year = extract_year_from_filename(pdf_name)
        school_name, location = get_school_and_location(pdf_name)
        extracted_date = get_extracted_date()

        doc = fitz.open(pdf_path)
        page = doc.load_page(page_number)
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        frame = np.array(img)

        face_locations = face_recognition.face_locations(frame)
        if len(face_locations) == 0 or is_collage(face_locations):
            return []

        for i, face_location in enumerate(face_locations):
            top, right, bottom, left = face_location
            face_image = frame[top:bottom, left:right]
            if face_image.size == 0:
                continue

            face_pil = Image.fromarray(face_image).resize(TARGET_SIZE)
            face_filename = f"{pdf_name}_page{page_number}_face{i}.jpg"
            face_path = os.path.join(OUTPUT_FOLDER, face_filename)
            face_pil.save(face_path)

            face_encoding = face_recognition.face_encodings(frame, known_face_locations=[face_location])
            if face_encoding:
                encoding = np.asarray(face_encoding[0], dtype=np.float64)
                if encoding.shape == (128,):
                    results.append((
                        face_filename,
                        page_number,
                        face_path,
                        school_name,
                        year,
                        location,
                        extracted_date,
                        encoding
                    ))
                    print(f"[✓] {face_filename}")
                else:
                    print(f"[×] {face_filename} — bad shape: {encoding.shape}")
            else:
                print(f"[×] {face_filename} — no encoding")

    except Exception as e:
        print(f"Error on page {page_number}: {e}")
    
    return results

def process_pdf_parallel(pdf_path):
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"\n⚙️ Processing {total_pages} pages using {multiprocessing.cpu_count()} CPU cores...\n")

    with ProcessPoolExecutor() as executor:
        all_args = [(pdf_path, i) for i in range(total_pages)]
        results = executor.map(process_page, all_args)

    flattened = [item for sublist in results for item in sublist]
    return flattened

def save_to_sqlite(entries, db_path):
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        page_number INTEGER,
        image_path TEXT,
        school_name TEXT,
        year TEXT,
        location TEXT,
        extracted_date TEXT,
        encoding BLOB
    )
    """)

    inserted = 0
    for entry in entries:
        try:
            filename, page_number, image_path, school_name, year, location, extracted_date, encoding = entry

            enc_blob = pickle.dumps(np.asarray(encoding, dtype=np.float64), protocol=pickle.HIGHEST_PROTOCOL)
            cursor.execute("""
                INSERT INTO faces (filename, page_number, image_path, school_name, year, location, extracted_date, encoding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (filename, page_number, image_path, school_name, year, location, extracted_date, enc_blob))
            inserted += 1
        except Exception as e:
            print(f"❌ Failed to insert {filename}: {e}")

    conn.commit()
    conn.close()
    print(f"\n✅ Saved {inserted} valid face encodings to SQLite DB at {db_path}")

def main():
    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")]
    for i, file in enumerate(pdf_files):
        print(f"{i}: {file}")
    choice = input("Enter the number of the PDF you want to process: ")
    try:
        selected_pdf = os.path.join(PDF_FOLDER, pdf_files[int(choice)])
    except:
        print("Invalid choice.")
        return

    entries = process_pdf_parallel(selected_pdf)
    if entries:
        save_to_sqlite(entries, DB_PATH)
    else:
        print("No valid faces extracted.")

if __name__ == "__main__":
    main()
