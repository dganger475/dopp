import logging
import multiprocessing
import os
import re
import sqlite3
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import face_recognition
from pdf2image import convert_from_path
from PIL import Image, ImageOps
from tqdm import tqdm

import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
TEST_PDF = Path(r"C:\Users\1439\Documents\DopplegangerApp\downloads").glob("*.pdf").__next__()  # Gets first PDF
OUTPUT_DIR = Path("test_extracted_faces")
FACE_PROXIMITY_THRESHOLD = 80  # For detecting group photos
PADDING = 40
TARGET_SIZE = (300, 300)
DPI = 400
NUM_CORES = 20  # Number of cores to use

def extract_metadata(pdf_path):
    """Extract year and school from filename"""
    filename = pdf_path.stem
    
    # Extract year
    year_match = re.search(r'(\d{4})', filename)
    year = year_match.group(1) if year_match else "UnknownYear"
    
    # Extract school name
    # Remove year and common words
    school_name = filename.replace(year, '').replace('Yearbook', '').replace('_', ' ').strip()
    if not school_name:
        school_name = "UnknownSchool"
    
    return school_name, year

def is_group_photo(face_locations):
    """Determine if image is likely a group photo based on face proximity"""
    if len(face_locations) > 20:  # Allow more faces per page, typical for yearbook grids
        return True
        
    # Skip proximity check for pages with 12 or fewer faces (typical yearbook grid layout)
    if len(face_locations) <= 12:
        return False
        
    centers = []
    for top, right, bottom, left in face_locations:
        centers.append(((left + right) / 2, (top + bottom) / 2))
    
    # Count how many faces are too close to each other
    close_faces = 0
    for i, (x1, y1) in enumerate(centers):
        for j, (x2, y2) in enumerate(centers):
            if i != j:
                dist = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                if dist < 40:  # Reduced from 80 to 40 for tighter threshold
                    close_faces += 1
    
    # Only consider it a group photo if more than 30% of faces are too close
    return close_faces > (len(face_locations) * 0.3)

def is_low_quality(face_img):
    """Check if face image is too small, dark, or blurry"""
    gray = np.mean(face_img, axis=2)
    brightness = np.mean(gray)
    contrast = np.std(gray)
    
    # Relaxed quality thresholds
    too_small = face_img.shape[0] < 40 or face_img.shape[1] < 40  # Reduced from 50
    too_dark = brightness < 40  # Reduced from 50
    too_flat = contrast < 10  # Reduced from 15
    
    return too_small or too_dark or too_flat

def process_face(args):
    """Process a single face - used by parallel processing"""
    try:
        image_np, face_loc, metadata = args
        top, right, bottom, left = face_loc
        height, width = image_np.shape[:2]
        school_name, year, page_num, face_idx = metadata

        # Add padding
        top = max(0, top - PADDING)
        right = min(width, right + PADDING)
        bottom = min(height, bottom + PADDING)
        left = max(0, left - PADDING)
        
        # Extract face
        face_img = image_np[top:bottom, left:right]
        
        if is_low_quality(face_img):
            return None
            
        # Convert to PIL and resize
        face_pil = Image.fromarray(face_img)
        face_pil = ImageOps.fit(face_pil, TARGET_SIZE, method=Image.LANCZOS)
        
        # Create filename with metadata
        filename = f"{school_name}_{year}_page{page_num + 1}_face{face_idx + 1}.jpg"
        filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        face_path = OUTPUT_DIR / filename
        
        face_pil.save(face_path, quality=95)
        return filename
        
    except Exception as e:
        logging.error(f"Error processing face: {e}")
        return None

def process_page(args):
    """Process a single page - used by parallel processing"""
    try:
        page, page_num, school_name, year = args
        image_np = np.array(page)
        face_locations = face_recognition.face_locations(image_np)
        
        if not face_locations or is_group_photo(face_locations):
            return []
            
        # Prepare face processing tasks
        face_tasks = []
        for face_idx, face_loc in enumerate(face_locations):
            metadata = (school_name, year, page_num, face_idx)
            face_tasks.append((image_np, face_loc, metadata))
            
        # Process faces in parallel
        with ProcessPoolExecutor(max_workers=NUM_CORES) as executor:
            results = list(executor.map(process_face, face_tasks))
            
        return [r for r in results if r is not None]
        
    except Exception as e:
        logging.error(f"Error processing page {page_num + 1}: {e}")
        return []

def process_yearbook(pdf_path):
    """Process a single yearbook PDF with parallel processing"""
    try:
        OUTPUT_DIR.mkdir(exist_ok=True)
        school_name, year = extract_metadata(pdf_path)
        logging.info(f"\nProcessing yearbook: {school_name} ({year})")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Convert PDF to images
            pages = convert_from_path(str(pdf_path), dpi=DPI, output_folder=temp_dir)
            logging.info(f"Converted {len(pages)} pages")
            
            # Prepare page processing tasks
            page_tasks = [(page, idx, school_name, year) for idx, page in enumerate(pages)]
            
            # Process pages in parallel
            processed_files = []
            with ProcessPoolExecutor(max_workers=NUM_CORES) as executor:
                futures = [executor.submit(process_page, task) for task in page_tasks]
                
                # Show progress bar
                with tqdm(total=len(pages), desc="Processing pages") as pbar:
                    for future in as_completed(futures):
                        processed_files.extend(future.result())
                        pbar.update(1)
            
            logging.info(f"Extracted {len(processed_files)} faces")
            for filename in processed_files:
                logging.info(f"Extracted: {filename}")
                
    except Exception as e:
        logging.error(f"Error processing yearbook {pdf_path}: {e}")

if __name__ == "__main__":
    multiprocessing.freeze_support()  # Required for Windows
    if not TEST_PDF.exists():
        logging.error("No PDF files found in downloads folder!")
    else:
        logging.info(f"Testing with: {TEST_PDF.name}")
        process_yearbook(TEST_PDF)
        logging.info("Test extraction complete. Check test_extracted_faces folder.") 