
import argparse
import datetime
import json
import logging
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import face_recognition
from pdf2image import convert_from_path
from PIL import Image, ImageFilter, ImageStat

import numpy as np

# === Config ===
PDF_DIRECTORY = Path(r"C:/Users/1439/Documents/DopplegangerApp/downloads")
FACES_FOLDER = Path(r"C:/Users/1439/Documents/DopplegangerApp/static/extracted_faces")
DATABASE_FILE = Path(r"C:/Users/1439/Documents/DopplegangerApp/faces.db")
CHECKPOINT_FILE = Path("processed_log.json")
MAX_WORKERS = 6  # Adjust based on CPU

PDF_DIRECTORY.mkdir(parents=True, exist_ok=True)
FACES_FOLDER.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def connect_db():
    return sqlite3.connect(str(DATABASE_FILE))

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

def enhance_face_image(image):
    from PIL import ImageEnhance
    from skimage import exposure

    if image.mode != 'RGB':
        image = image.convert('RGB')

    aspect = image.width / image.height
    new_width = 600 if aspect > 1 else int(600 * aspect)
    new_height = 600 if aspect <= 1 else int(600 / aspect)
    image = image.resize((new_width, new_height), Image.LANCZOS)

    new_img = Image.new('RGB', (600, 600), (255, 255, 255))
    x_offset = (600 - new_width) // 2
    y_offset = (600 - new_height) // 2
    new_img.paste(image, (x_offset, y_offset))

    try:
        img_array = np.array(new_img)
        for channel in range(3):
            img_array[:, :, channel] = exposure.equalize_adapthist(
                img_array[:, :, channel], clip_limit=0.03) * 255
        new_img = Image.fromarray(img_array.astype('uint8'))

        r, g, b = new_img.split()
        r_avg = ImageStat.Stat(r).mean[0]
        g_avg = ImageStat.Stat(g).mean[0]
        b_avg = ImageStat.Stat(b).mean[0]
        avg = (r_avg + g_avg + b_avg) / 3

        r = r.point(lambda i: i * (avg / r_avg) if r_avg > 0 else i)
        g = g.point(lambda i: i * (avg / g_avg) if g_avg > 0 else i)
        b = b.point(lambda i: i * (avg / b_avg) if b_avg > 0 else i)
        new_img = Image.merge('RGB', (r, g, b))

        new_img = new_img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        enhancer = ImageEnhance.Contrast(new_img)
        new_img = enhancer.enhance(1.2)
        new_img = new_img.filter(ImageFilter.MedianFilter(size=3))
        new_img = new_img.filter(ImageFilter.EDGE_ENHANCE)
        enhancer = ImageEnhance.Color(new_img)
        new_img = enhancer.enhance(1.1)
        enhancer = ImageEnhance.Brightness(new_img)
        new_img = enhancer.enhance(1.05)

    except Exception as e:
        logging.error(f"Enhancement failed: {e}")
    return new_img

def assess_image_quality(image):
    gray = image.convert('L')
    stat = ImageStat.Stat(gray)
    contrast = stat.stddev[0]
    brightness = stat.mean[0]

    sharpness = ImageStat.Stat(image.filter(ImageFilter.FIND_EDGES)).stddev[0]

    score = (sharpness * 0.5) + (contrast * 0.3) + (brightness / 255 * 0.2)

    if sharpness < 5:
        flag = "blurry"
    elif contrast < 15:
        flag = "low_contrast"
    elif brightness < 40:
        flag = "dark"
    else:
        flag = "good"

    return score, flag

def process_pdf(pdf_path):
    filename = pdf_path.name
    parts = filename.split("_")
    year, school, location = (parts[0], parts[1], "_".join(parts[2:-1])) if len(parts) >= 4 else ("Unknown", "Unknown", "Unknown")
    pages = []

    try:
        pages = convert_from_path(str(pdf_path), dpi=200)
    except Exception as e:
        logging.error(f"Could not read {filename}: {e}")
        return filename, False

    conn = connect_db()
    create_table(conn)
    saved_any = False

    for page_num, page in enumerate(pages, start=1):
        img_array = np.array(page.convert("RGB"))
        face_locations = face_recognition.face_locations(img_array, model='hog')
        face_encodings = face_recognition.face_encodings(img_array, face_locations)

        for idx, (loc, encoding) in enumerate(zip(face_locations, face_encodings)):
            top, right, bottom, left = loc
            pad = int(max(bottom - top, right - left) * 0.3)
            top = max(0, top - pad)
            bottom = min(img_array.shape[0], bottom + pad)
            left = max(0, left - pad)
            right = min(img_array.shape[1], right + pad)

            face_img = Image.fromarray(img_array[top:bottom, left:right])
            enhanced = enhance_face_image(face_img)
            score, flag = assess_image_quality(enhanced)

            face_filename = f"{filename}_page_{page_num}_face_{idx+1}.jpg"
            face_path = FACES_FOLDER / face_filename
            enhanced.save(face_path, 'JPEG', quality=95)

            try:
                conn.execute('''
                    INSERT INTO faces (filename, image_path, encoding, extracted_date,
                                       page_number, school, year, location,
                                       quality_score, quality_flag)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (face_filename, str(face_path), encoding.tobytes(),
                      datetime.datetime.now().isoformat(), page_num, school, year, location,
                      score, flag))
                conn.commit()
                saved_any = True
            except Exception as e:
                logging.error(f"Failed to save face {face_filename}: {e}")

    conn.close()
    return filename, saved_any

def load_checkpoint():
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_checkpoint(log):
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)

def extract_faces_in_parallel(start=0, end=None):
    all_pdfs = sorted([p for p in PDF_DIRECTORY.glob("*.pdf")])
    if end:
        all_pdfs = all_pdfs[start:end]
    else:
        all_pdfs = all_pdfs[start:]

    log = load_checkpoint()
    to_process = [pdf for pdf in all_pdfs if pdf.name not in log or not log[pdf.name]]

    logging.info(f"Processing {len(to_process)} new PDFs...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_pdf, pdf): pdf.name for pdf in to_process}
        for future in futures:
            fname, success = future.result()
            log[fname] = success
            save_checkpoint(log)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0, help="Start index in PDF list")
    parser.add_argument("--end", type=int, default=None, help="End index in PDF list")
    args = parser.parse_args()

    extract_faces_in_parallel(args.start, args.end)
