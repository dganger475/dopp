import os
import pickle

import cv2
import face_recognition
import fitz  # PyMuPDF
from PIL import Image

import numpy as np

# -------- CONFIG --------
PDF_FOLDER = r"C:\Users\1439\Documents\DopplegangerApp\downloads"
OUTPUT_FOLDER = r"static\extracted_faces"
DB_PATH = "faces.db"
TARGET_SIZE = (300, 300)
MAX_FACES_PER_PAGE = 15  # Skip collage-like pages
# ------------------------

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def is_collage(face_locations, threshold=0.20):
    """Skip images where too many faces are too close together."""
    for i, (top1, right1, bottom1, left1) in enumerate(face_locations):
        for j, (top2, right2, bottom2, left2) in enumerate(face_locations):
            if i != j:
                dist = np.sqrt((left1 - left2) ** 2 + (top1 - top2) ** 2)
                if dist < threshold * TARGET_SIZE[0]:
                    return True
    return False

def process_pdf(pdf_path):
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    doc = fitz.open(pdf_path)
    all_encodings = []
    all_names = []
    print(f"Processing: {pdf_name}")

    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        frame = np.array(img)

        face_locations = face_recognition.face_locations(frame)

        if len(face_locations) == 0 or len(face_locations) > MAX_FACES_PER_PAGE or is_collage(face_locations):
            continue

        for i, face_location in enumerate(face_locations):
            top, right, bottom, left = face_location
            face_image = frame[top:bottom, left:right]
            if face_image.size == 0:
                continue

            face_pil = Image.fromarray(face_image).resize(TARGET_SIZE)
            face_filename = f"{pdf_name}_page{page_number}_face{i}.jpg"
            face_path = os.path.join(OUTPUT_FOLDER, face_filename)
            face_pil.save(face_path)

            encoding = face_recognition.face_encodings(np.array(face_pil))
            if encoding:
                all_encodings.append(encoding[0])
                all_names.append(face_filename)
                print(f"Saved: {face_filename}")
            else:
                print(f"Skipped: {face_filename} (no encoding)")

    return all_encodings, all_names

def save_db(encodings, names, db_path):
    data = {"encodings": encodings, "names": names}
    with open(db_path, "wb") as f:
        pickle.dump(data, f)
    print(f"Saved {len(encodings)} encodings to {db_path}")

def main():
    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print("No PDFs found.")
        return

    test_pdf = os.path.join(PDF_FOLDER, pdf_files[0])
    print(f"Testing with: {test_pdf}")

    encodings, names = process_pdf(test_pdf)
    save_db(encodings, names, DB_PATH)

if __name__ == "__main__":
    main()
