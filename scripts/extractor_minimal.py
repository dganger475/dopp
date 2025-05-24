
import argparse
import datetime
import json
import logging
import os
import pickle
import sqlite3
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import face_recognition
import faiss
from pdf2image import convert_from_path
from PIL import Image
from tqdm import tqdm

import numpy as np

PDF_DIRECTORY = Path(r"C:/Users/1439/Documents/DopplegangerApp/downloads")
FACES_FOLDER = Path(r"C:/Users/1439/Documents/DopplegangerApp/static/extracted_faces")
DATABASE_FILE = Path(r"C:/Users/1439/Documents/DopplegangerApp/faces.db")
CHECKPOINT_FILE = Path("processed_log.json")
INDEX_FILE = Path("faces.index")
META_FILE = Path("faces_meta.pkl")
MAX_WORKERS = os.cpu_count() or 4

PDF_DIRECTORY.mkdir(parents=True, exist_ok=True)
FACES_FOLDER.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def basic_crop_resize_pad(image_np, loc, page_size):
    top, right, bottom, left = loc
    pad = int(max(bottom - top, right - left) * 0.3)
    top = max(0, top - pad)
    bottom = min(page_size[0], bottom + pad)
    left = max(0, left - pad)
    right = min(page_size[1], right + pad)

    face_img = Image.fromarray(image_np[top:bottom, left:right]).convert("RGB")

    aspect = face_img.width / face_img.height
    new_width = 600 if aspect > 1 else int(600 * aspect)
    new_height = 600 if aspect <= 1 else int(600 / aspect)
    resized = face_img.resize((new_width, new_height), Image.LANCZOS)

    padded = Image.new('RGB', (600, 600), (255, 255, 255))
    x_offset = (600 - new_width) // 2
    y_offset = (600 - new_height) // 2
    padded.paste(resized, (x_offset, y_offset))
    return padded

def process_pdf(pdf_path_str):
    pdf_path = Path(pdf_path_str)
    filename = pdf_path.name
    parts = filename.split("_")
    year, school, location = (parts[0], parts[1], "_".join(parts[2:-1])) if len(parts) >= 4 else ("Unknown", "Unknown", "Unknown")

    try:
        pages = convert_from_path(str(pdf_path), dpi=200)
    except Exception as e:
        return filename, 0, 0, []

    results = []
    for page_num, page in enumerate(pages, start=1):
        img_array = np.array(page.convert("RGB"))
        face_locations = face_recognition.face_locations(img_array, model='hog')
        face_encodings = face_recognition.face_encodings(img_array, face_locations)

        for idx, (loc, encoding) in enumerate(zip(face_locations, face_encodings)):
            try:
                face_image = basic_crop_resize_pad(img_array, loc, img_array.shape)
                face_filename = f"{filename}_page_{page_num}_face_{idx+1}.jpg"
                face_path = FACES_FOLDER / face_filename
                face_image.save(face_path, 'JPEG', quality=95)

                results.append({
                    "filename": face_filename,
                    "image_path": str(face_path),
                    "page_number": page_num,
                    "encoding": encoding.tobytes(),
                    "extracted_date": datetime.datetime.now().isoformat(),
                    "school": school,
                    "year": year,
                    "location_info": location,
                    "score": None,
                    "flag": "unknown"
                })
            except Exception as e:
                logging.error(f"Failed to process face {idx+1} on page {page_num}: {e}")

    return filename, len(results), results

def extract_faces_parallel(start=0, end=None):
    all_pdfs = sorted([p for p in PDF_DIRECTORY.glob("*.pdf")])
    selected = all_pdfs[start:end] if end else all_pdfs[start:]

    log = {}
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            log = json.load(f)

    to_process = [p for p in selected if p.name not in log or not log[p.name]]

    index, metadata = load_faiss()

    print(f"📄 Processing {len(to_process)} PDFs with {MAX_WORKERS} workers...")
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_pdf, str(pdf)): pdf.name for pdf in to_process}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing PDFs"):
            fname, total, results = future.result()
            conn = sqlite3.connect(str(DATABASE_FILE))
            create_table(conn)
            for face in results:
                try:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO faces (filename, image_path, encoding, extracted_date,
                                           page_number, school, year, location,
                                           quality_score, quality_flag)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (face["filename"], face["image_path"], face["encoding"],
                          face["extracted_date"], face["page_number"],
                          face["school"], face["year"], face["location_info"],
                          face["score"], face["flag"]))
                    conn.commit()
                    face_id = cursor.lastrowid
                    index.add(np.array([np.frombuffer(face["encoding"], dtype=np.float32)]))
                    metadata.append({"id": face_id, "filename": face["filename"]})
                except Exception as e:
                    logging.error(f"Failed to insert face {face['filename']}: {e}")
            conn.close()
            log[fname] = True
            with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
                json.dump(log, f, indent=2)

    save_faiss(index, metadata)

def create_table(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS faces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            image_path TEXT,
            encoding BLOB,
            extracted_date TEXT,
            page_number INTEGER,
            school TEXT,
            year TEXT,
            location TEXT,
            quality_score REAL,
            quality_flag TEXT
        )
    ''')
    conn.commit()

def load_faiss():
    if INDEX_FILE.exists() and META_FILE.exists():
        index = faiss.read_index(str(INDEX_FILE))
        with open(META_FILE, "rb") as f:
            meta = pickle.load(f)
    else:
        index = faiss.IndexFlatL2(128)
        meta = []
    return index, meta

def save_faiss(index, metadata):
    faiss.write_index(index, str(INDEX_FILE))
    with open(META_FILE, "wb") as f:
        pickle.dump(metadata, f)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=None)
    args = parser.parse_args()

    extract_faces_parallel(args.start, args.end)
