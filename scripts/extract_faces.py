import bz2
import hashlib
import logging
import os
import sqlite3
from datetime import datetime

import cv2
import dlib
import face_recognition
import requests
from deepface import DeepFace
from mtcnn import MTCNN
from pdf2image import convert_from_path
from PIL import Image
from PyPDF2 import PdfReader
from tqdm import tqdm

import numpy as np

from app_config import DB_PATH, SORTED_FACES, MODELS_DIR

# Model configuration
MODEL_PATH = os.path.join(MODELS_DIR, 'shape_predictor_68_face_landmarks.dat')
FACE_LANDMARK_MODEL = {
    'url': 'https://github.com/davisking/dlib-models/raw/master/shape_predictor_68_face_landmarks.dat.bz2',
    'filename': 'shape_predictor_68_face_landmarks.dat',
    'compressed_filename': 'shape_predictor_68_face_landmarks.dat.bz2',
    'checksum': '7da233e5ca8bb5c267bda3dcc8f29226'  # Updated MD5 checksum
}

# Processing configuration
CHUNK_SIZE = 10
RESIZE_SIZE = (300, 300)
MIN_FACE_SIZE = 80  # Minimum face dimension in pixels
MIN_CONFIDENCE = 0.95  # Minimum detection confidence
MIN_QUALITY_SCORE = 0.5  # Minimum quality score

# Ensure directories exist
os.makedirs(SORTED_FACES, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_model():
    """Download and setup required model files"""
    if os.path.exists(MODEL_PATH):
        return
    
    print("Downloading face landmark model...")
    compressed_path = os.path.join(MODELS_DIR, FACE_LANDMARK_MODEL['compressed_filename'])
    
    try:
        # Download the compressed model
        response = requests.get(FACE_LANDMARK_MODEL['url'], stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024
        
        with open(compressed_path, 'wb') as f, tqdm(
            desc="Downloading model",
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for data in response.iter_content(block_size):
                size = f.write(data)
                pbar.update(size)
        
        # Verify checksum
        print("Verifying download...")
        with open(compressed_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        
        if file_hash != FACE_LANDMARK_MODEL['checksum']:
            print(f"Warning: Checksum verification failed. Expected {FACE_LANDMARK_MODEL['checksum']}, got {file_hash}")
            print("Proceeding with extraction anyway...")
        
        # Extract the bz2 file
        print("Extracting model file...")
        with bz2.BZ2File(compressed_path) as compressed, open(MODEL_PATH, 'wb') as output:
            output.write(compressed.read())
        
        # Clean up compressed file
        os.remove(compressed_path)
        print("Face landmark model downloaded and extracted successfully")
        
        # Verify the extracted file exists and has content
        if not os.path.exists(MODEL_PATH) or os.path.getsize(MODEL_PATH) == 0:
            raise ValueError("Extracted model file is missing or empty")
            
    except Exception as e:
        print(f"Error downloading model: {str(e)}")
        # Clean up any partial downloads
        if os.path.exists(compressed_path):
            os.remove(compressed_path)
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)
        raise

# Download model if needed
try:
    download_model()
except Exception as e:
    print(f"Failed to download model: {str(e)}")
    print("Please download the shape_predictor_68_face_landmarks.dat file manually and place it in the models directory")
    exit(1)

# Initialize face detectors
print("Initializing face detectors...")
mtcnn_detector = MTCNN()
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(MODEL_PATH)

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    return conn

def create_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            image_path TEXT,
            encoding BLOB,
            extracted_date TEXT,
            page_number INTEGER,
            school TEXT,
            year TEXT,
            location TEXT,
            gender TEXT,
            race TEXT,
            quality_score REAL
        )
    ''')
    conn.commit()
    logging.info("Database table created or already exists.")

def generate_filename(metadata, page, face_num):
    base_name = f"{metadata['year']}_{metadata['school_name'].replace(' ', '_')}_{metadata['location'].replace(' ', '_')}_page_{page}_face_{face_num}.jpg"
    folder_path = os.path.join(SORTED_FACES, metadata['gender'], metadata['race'])
    os.makedirs(folder_path, exist_ok=True)
    
    filename = os.path.join(folder_path, base_name)
    counter = 1
    while os.path.exists(filename):
        filename = os.path.join(folder_path, f"{metadata['year']}_{metadata['school_name'].replace(' ', '_')}_{metadata['location'].replace(' ', '_')}_page_{page}_face_{face_num}_{counter}.jpg")
        counter += 1
    
    return filename

def assess_face_quality(face_img):
    """Assess the quality of the extracted face."""
    try:
        # Convert to grayscale
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        
        # Calculate quality metrics
        sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
        brightness = np.mean(gray)
        contrast = np.std(gray)
        
        # Check face size
        height, width = face_img.shape[:2]
        size_score = min(width, height) / MIN_FACE_SIZE
        
        # Normalize and combine scores
        sharpness_score = min(sharpness / 1000, 1.0)
        brightness_score = 1.0 - abs(brightness - 128) / 128
        contrast_score = min(contrast / 64, 1.0)
        
        # Weighted quality score
        quality_score = (sharpness_score * 0.4 + 
                        brightness_score * 0.2 + 
                        contrast_score * 0.2 + 
                        size_score * 0.2)
        
        return quality_score
        
    except Exception as e:
        logging.error(f"Error assessing face quality: {e}")
        return 0.0

def align_face(image, landmarks):
    """Align face based on eye positions."""
    try:
        left_eye = np.mean(landmarks['left_eye'], axis=0)
        right_eye = np.mean(landmarks['right_eye'], axis=0)
        
        # Calculate angle for alignment
        angle = np.degrees(np.arctan2(right_eye[1] - left_eye[1],
                                    right_eye[0] - left_eye[0]))
        
        # Rotate image
        center = tuple(np.array(image.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
        aligned = cv2.warpAffine(image, rot_mat, image.shape[1::-1],
                                flags=cv2.INTER_CUBIC)
        return aligned
    except Exception as e:
        logging.error(f"Face alignment failed: {e}")
        return image

def extract_faces(pdf_path, metadata):
    """Processes the PDF and extracts faces using MTCNN."""
    conn = connect_db()
    create_table(conn)

    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    faces_extracted = 0
    faces_rejected = 0

    for start_page in range(1, total_pages + 1, CHUNK_SIZE):
        end_page = min(start_page + CHUNK_SIZE - 1, total_pages)
        pages = convert_from_path(pdf_path, first_page=start_page, last_page=end_page)

        for page_num, page in enumerate(pages):
            current_page = start_page + page_num
            
            # Convert PIL Image to numpy array
            img_array = np.array(page)
            
            # Detect faces using MTCNN
            detections = mtcnn_detector.detect_faces(img_array)
            
            for i, detection in enumerate(detections):
                if detection['confidence'] < MIN_CONFIDENCE:
                    faces_rejected += 1
                    continue
                    
                # Extract face coordinates
                x, y, w, h = detection['box']
                
                # Add margin around face
                margin = int(max(w, h) * 0.2)
                x = max(0, x - margin)
                y = max(0, y - margin)
                w = min(img_array.shape[1] - x, w + 2 * margin)
                h = min(img_array.shape[0] - y, h + 2 * margin)
                
                # Extract and process face
                face_image = img_array[y:y + h, x:x + w]
                
                # Align face using landmarks
                if 'keypoints' in detection:
                    face_image = align_face(face_image, detection['keypoints'])
                
                # Resize face
                face_image = cv2.resize(face_image, RESIZE_SIZE)
                
                # Assess face quality
                quality_score = assess_face_quality(face_image)
                if quality_score < MIN_QUALITY_SCORE:
                    faces_rejected += 1
                    continue
                
                # Analyze face attributes
                try:
                    analysis = DeepFace.analyze(img_path=face_image, 
                                              actions=["gender", "race"],
                                              enforce_detection=False)
                    gender = analysis[0]['dominant_gender']
                    race = analysis[0]['dominant_race']
                except Exception as e:
                    logging.error(f"Face analysis failed: {e}")
                    gender = "Unknown"
                    race = "Unknown"
                
                metadata.update({"gender": gender, "race": race})
                filename = generate_filename(metadata, current_page, i + 1)
                image_path = filename.replace(SORTED_FACES + os.sep, "sorted_faces/")
                
                # Save face image
                cv2.imwrite(filename, cv2.cvtColor(face_image, cv2.COLOR_RGB2BGR))
                
                # Generate face encoding
                encoding = face_recognition.face_encodings(face_image)
                if encoding:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR IGNORE INTO faces 
                        (filename, image_path, encoding, extracted_date, page_number, 
                         school, year, location, gender, race, quality_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (image_path, filename, encoding[0].tobytes(), 
                         metadata["extracted_date"], current_page, 
                         metadata["school_name"], metadata["year"], 
                         metadata["location"], gender, race, quality_score))
                    conn.commit()
                    faces_extracted += 1
                    logging.info(f"Face extracted and saved: {filename} (Quality: {quality_score:.2f})")
                else:
                    faces_rejected += 1
                    os.remove(filename)  # Remove file if encoding failed
    
    logging.info(f"Extraction complete: {faces_extracted} faces extracted, {faces_rejected} faces rejected")
    conn.close()
