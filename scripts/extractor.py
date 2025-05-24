import logging
import multiprocessing
import os
import re
import sqlite3
import traceback
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime

import face_recognition
import fitz  # PyMuPDF
from PIL import Image
from tqdm import tqdm

import numpy as np

# ─────────────────────────────────────────────
PDF_FOLDER = r"C:\Users\1439\Documents\DopplegangerApp\Just Pic PDF"
OUTPUT_FOLDER = r"C:\Users\1439\Documents\DopplegangerApp\static\extracted_faces"
DB_PATH = r"C:\Users\1439\Documents\DopplegangerApp\faces.db"
LOG_PATH = r"C:\Users\1439\Documents\DopplegangerApp\extractor.log"
PADDING_RATIO = 0.6
FINAL_SIZE = (300, 300)
NUM_WORKERS = 4

# ─────────────────────────────────────────────
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(
    filename=LOG_PATH,
    filemode='w',
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def ensure_db_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            encoding BLOB,
            yearbook_year TEXT,
            school_name TEXT,
            page_number INTEGER,
            face_number INTEGER,
            quality_score REAL,
            quality_flag TEXT,
            extracted_date TEXT
        )
    """)
    conn.commit()
    conn.close()

def already_processed(filename):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM faces WHERE filename = ?", (filename,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception as e:
        logging.error(f"❌ DB check failed for {filename}: {e}")
        return False

def parse_filename_components(base_filename, page_num, face_num):
    base_name = os.path.splitext(base_filename)[0]
    return f"static/extracted_faces/{base_name}_p{page_num}_f{face_num}.jpg"

def process_pdf(pdf_path):
    try:
        logging.info(f"🔍 Starting: {pdf_path}")
        entries = []
        base_filename = os.path.basename(pdf_path)
        yearbook_year = re.search(r'(19|20)\d{2}', base_filename)
        yearbook_year = yearbook_year.group(0) if yearbook_year else "Unknown"
        school_name = base_filename.replace('.pdf', '').replace(yearbook_year, '').replace('_', ' ').strip()
        extracted_date = datetime.now().strftime("%Y-%m-%d")

        pdf_doc = fitz.open(pdf_path)
        for page_number in range(len(pdf_doc)):
            try:
                page = pdf_doc.load_page(page_number)
                pix = page.get_pixmap(dpi=300)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img_array = np.array(img)

                logging.info(f"🧠 face_recognition on page {page_number + 1} of {base_filename}")
                face_locations = face_recognition.face_locations(img_array)

                for idx, (top, right, bottom, left) in enumerate(face_locations):
                    save_filename = parse_filename_components(base_filename, page_number + 1, idx + 1)
                    full_save_path = os.path.join(r"C:\Users\1439\Documents\DopplegangerApp", save_filename)

                    if already_processed(save_filename):
                        logging.info(f"⏩ Skipped existing face: {save_filename}")
                        continue

                    height = bottom - top
                    width = right - left
                    pad_h = int(height * PADDING_RATIO)
                    pad_w = int(width * PADDING_RATIO)
                    top = max(0, top - pad_h)
                    bottom = min(img_array.shape[0], bottom + pad_h)
                    left = max(0, left - pad_w)
                    right = min(img_array.shape[1], right + pad_w)

                    face_crop = img_array[top:bottom, left:right]
                    face_img = Image.fromarray(face_crop).resize(FINAL_SIZE, Image.LANCZOS)

                    os.makedirs(os.path.dirname(full_save_path), exist_ok=True)
                    face_img.save(full_save_path)

                    encodings = face_recognition.face_encodings(np.array(face_img))
                    if encodings:
                        encoding_bytes = encodings[0].astype(np.float64).tobytes()
                        entries.append((save_filename, encoding_bytes, yearbook_year, school_name,
                                        page_number + 1, idx + 1, 1.0, 'good', extracted_date))
            except Exception as e:
                logging.error(f"❌ Page {page_number + 1} error in {pdf_path}: {e}")

        logging.info(f"✅ Finished: {pdf_path} → {len(entries)} new faces")
        return entries

    except Exception as e:
        logging.error(f"❌ Crash in process_pdf for {pdf_path}:\n{traceback.format_exc()}")
        return []

def insert_entries(entries):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT OR IGNORE INTO faces (
            filename, encoding, yearbook_year, school_name,
            page_number, face_number, quality_score, quality_flag, extracted_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, entries)
    conn.commit()
    conn.close()

def main():
    ensure_db_table()
    if not os.path.exists(PDF_FOLDER):
        logging.error(f"❌ PDF folder not found: {PDF_FOLDER}")
        return

    pdf_files = [os.path.join(PDF_FOLDER, f) for f in os.listdir(PDF_FOLDER) if f.lower().endswith('.pdf')]
    logging.info(f"📄 Found {len(pdf_files)} PDFs")

    results = []
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(process_pdf, pdf): pdf for pdf in pdf_files}
        for future in tqdm(futures, total=len(futures), desc="Processing PDFs"):
            try:
                result = future.result()
                results.extend(result)
            except Exception as e:
                logging.error(f"❌ Failed processing {futures[future]}: {e}")

    logging.info(f"\n✅ Total new faces to insert: {len(results)}")
    if results:
        insert_entries(results)
        logging.info("✅ All new faces inserted into database.")
    else:
        logging.warning("⚠️ No new faces to insert.")

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    main()
