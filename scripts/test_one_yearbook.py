import multiprocessing
import os
import pickle
import sqlite3
from concurrent.futures import ProcessPoolExecutor

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

def is_collage(face_locations, threshold=0.12):
    for i, (top1, right1, bottom1, left1) in enumerate(face_locations):
        for j, (top2, right2, bottom2, left2) in enumerate(face_locations):
            if i != j:
                dist = np.sqrt((left1 - left2) ** 2 + (top1 - top2) ** 2)
                if dist < threshold * TARGET_SIZE[0]:
                    return True
    return False

def choose_pdf():
    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")]
    print("\nAvailable PDFs:\n")
    for i, file in enumerate(pdf_files):
        print(f"{i}: {file}")
    choice = input("\nEnter the number of the PDF you want to test: ")
    try:
        index = int(choice)
        return os.path.join(PDF_FOLDER, pdf_files[index])
    except:
        print("Invalid selection.")
        return None

def process_page(args):
    pdf_path, page_number = args
    results = []

    try:
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
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
                    results.append((face_filename, encoding))
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

    encodings = []
    filenames = []
    for page_results in results:
        for filename, encoding in page_results:
            filenames.append(filename)
            encodings.append(encoding)

    return encodings, filenames

def save_to_sqlite(encodings, filenames, db_path):
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        encoding BLOB
    )
    """)

    inserted = 0
    for filename, encoding in zip(filenames, encodings):
        try:
            encoding = np.asarray(encoding, dtype=np.float64)
            if encoding.shape != (128,):
                print(f"⚠️ Skipped {filename} — invalid shape {encoding.shape}")
                continue

            enc_blob = pickle.dumps(encoding, protocol=pickle.HIGHEST_PROTOCOL)

            # Optional test load
            test = pickle.loads(enc_blob)
            if not isinstance(test, np.ndarray) or test.shape != (128,):
                print(f"❌ {filename} failed re-load check")
                continue

            cursor.execute("INSERT INTO faces (filename, encoding) VALUES (?, ?)", (filename, enc_blob))
            inserted += 1

        except Exception as e:
            print(f"❌ Failed to store {filename}: {e}")

    conn.commit()
    conn.close()
    print(f"\n✅ Saved {inserted} valid face encodings to SQLite DB at {db_path}")

def main():
    selected_pdf = choose_pdf()
    if not selected_pdf:
        return

    encodings, filenames = process_pdf_parallel(selected_pdf)
    if encodings:
        save_to_sqlite(encodings, filenames, DB_PATH)
    else:
        print("No valid faces extracted.")

if __name__ == "__main__":
    main()
