import json
import logging
import multiprocessing
import os
import sqlite3
import warnings
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime

import cv2
from insightface.app import FaceAnalysis
from tqdm import tqdm

import numpy as np

# Suppress warnings and reduce logging noise
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)
logging.getLogger('insightface').setLevel(logging.ERROR)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Configuration
CACHE_FILE = "face_encodings_cache.json"
CHUNK_SIZE = 100  # Reduced from 1000 to 100
BATCH_SIZE = 10   # Process 10 faces at a time within each chunk
MAX_WORKERS = max(1, min(multiprocessing.cpu_count() - 1, 4))  # Limit to 4 cores max
SAVE_INTERVAL = 50  # Save results every 50 matches

def init_arcface():
    """Initialize ArcFace model quietly."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        app = FaceAnalysis(providers=['CPUExecutionProvider'], allowed_modules=['detection', 'recognition'])
        app.prepare(ctx_id=0, det_size=(640, 640))
    return app

def load_cache():
    """Load cached encodings."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    """Save encodings to cache."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def preprocess_face(image_path):
    """Enhance face image quality before encoding."""
    img = cv2.imread(image_path)
    if img is None:
        return None
        
    # Convert to RGB
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Enhance contrast
    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    l = clahe.apply(l)
    lab = cv2.merge((l,a,b))
    img = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    
    # Denoise
    img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)
    
    return img

def get_face_encoding(app, image_path, cache):
    """Get face encoding using ArcFace with enhanced preprocessing."""
    if image_path in cache:
        return np.array(cache[image_path])
    
    try:
        # Use enhanced preprocessing
        img = preprocess_face(image_path)
        if img is None:
            return None
            
        faces = app.get(img)
        if not faces:
            return None
        
        # Get the face with highest detection score
        best_face = max(faces, key=lambda x: x.det_score)
        encoding = best_face.embedding.tolist()
        cache[image_path] = encoding
        return np.array(encoding)
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return None

def calculate_similarity(encoding1, encoding2):
    """Calculate similarity using multiple metrics."""
    # Cosine similarity
    cosine_sim = np.dot(encoding1, encoding2) / (np.linalg.norm(encoding1) * np.linalg.norm(encoding2))
    cosine_sim = (cosine_sim + 1) / 2 * 100
    
    # Euclidean distance (converted to similarity)
    euclidean_dist = np.linalg.norm(encoding1 - encoding2)
    euclidean_sim = 100 * (1 - euclidean_dist / (2 * np.sqrt(len(encoding1))))
    
    # Combined similarity score (weighted average)
    similarity = cosine_sim * 0.7 + euclidean_sim * 0.3
    
    return similarity

def process_batch(args):
    """Process a small batch of faces."""
    batch_faces, all_faces, cache = args
    app = init_arcface()
    results = []
    local_cache = cache.copy()
    processed = 0
    
    for face1 in batch_faces:
        start_time = datetime.now()
        for face2 in all_faces:
            # Skip same face and same year/school combinations
            if (face1['filename'] == face2['filename'] or 
                (face1['year'] == face2['year'] and face1['school'] == face2['school'])):
                continue
            
            path1 = os.path.join("static", "extracted_faces", face1['filename'])
            path2 = os.path.join("static", "extracted_faces", face2['filename'])
            
            if not (os.path.exists(path1) and os.path.exists(path2)):
                continue
                
            encoding1 = get_face_encoding(app, path1, local_cache)
            encoding2 = get_face_encoding(app, path2, local_cache)
            
            if encoding1 is None or encoding2 is None:
                continue
            
            similarity = calculate_similarity(encoding1, encoding2)
            
            if similarity >= 70:
                results.append({
                    'face1': face1['filename'],
                    'face2': face2['filename'],
                    'similarity': float(similarity),
                    'year1': face1['year'],
                    'year2': face2['year'],
                    'school1': face1['school'],
                    'school2': face2['school']
                })
        
        processed += 1
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"Processed {face1['filename']} in {elapsed:.2f}s")
    
    return results, local_cache

def find_matches(year_range=None, min_similarity=70, same_school_only=False):
    """Find matches with additional filtering options."""
    print("Initializing...")
    
    # Load cache
    cache = load_cache()
    
    # Connect to database
    conn = sqlite3.connect("faces.db")
    cursor = conn.cursor()
    
    # Get faces with optional year filter
    if year_range:
        start_year, end_year = year_range
        cursor.execute("""
            SELECT filename, yearbook_year, school_name 
            FROM faces 
            WHERE CAST(yearbook_year AS INTEGER) BETWEEN ? AND ?
        """, (start_year, end_year))
    else:
        cursor.execute("SELECT filename, yearbook_year, school_name FROM faces")
    
    all_faces = [{'filename': f, 'year': y, 'school': s} for f, y, s in cursor.fetchall()]
    conn.close()
    
    total_faces = len(all_faces)
    print(f"Processing {total_faces} faces...")
    
    # Split faces into smaller batches
    batches = [all_faces[i:i + BATCH_SIZE] for i in range(0, len(all_faces), BATCH_SIZE)]
    print(f"Split into {len(batches)} batches of up to {BATCH_SIZE} faces each")
    
    # Process batches in parallel
    high_matches = []
    temp_results_file = "temp_matches.json"
    
    try:
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            for batch in batches:
                future = executor.submit(process_batch, (batch, all_faces, cache))
                futures.append(future)
            
            # Process results as they complete
            for i, future in enumerate(tqdm(futures, desc="Processing batches")):
                try:
                    batch_results, batch_cache = future.result(timeout=300)  # 5 minute timeout
                    high_matches.extend(batch_results)
                    cache.update(batch_cache)
                    
                    # Save intermediate results periodically
                    if len(high_matches) % SAVE_INTERVAL == 0:
                        print(f"\nSaving intermediate results ({len(high_matches)} matches so far)...")
                        with open(temp_results_file, 'w') as f:
                            json.dump(high_matches, f, indent=2)
                
                except Exception as e:
                    print(f"Error processing batch {i}: {e}")
                    continue
    
    except KeyboardInterrupt:
        print("\nProcessing interrupted. Saving partial results...")
    
    finally:
        # Save final results
        print("\nSaving final results...")
        unique_matches = []
        seen_pairs = set()
        
        for match in high_matches:
            pair = tuple(sorted([match['face1'], match['face2']]))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                unique_matches.append(match)
        
        unique_matches.sort(key=lambda x: x['similarity'], reverse=True)
        
        results_file = "high_similarity_matches.json"
        with open(results_file, 'w') as f:
            json.dump(unique_matches, f, indent=2)
        
        # Save final cache
        save_cache(cache)
        
        # Print summary
        print_results_summary(unique_matches)

def print_results_summary(unique_matches):
    """Print a summary of the results."""
    print("\nHigh Similarity Matches (70% or higher):")
    print("=" * 80)
    
    ranges = [(90, 100), (80, 90), (70, 80)]
    for range_min, range_max in ranges:
        range_matches = [m for m in unique_matches if range_min <= m['similarity'] < range_max]
        if range_matches:
            print(f"\n{range_min}-{range_max}% Similarity Matches ({len(range_matches)} found):")
            print("-" * 40)
            for match in range_matches[:5]:
                print(f"\nSimilarity: {match['similarity']:.2f}%")
                print(f"Face 1: {match['face1']}")
                print(f"Year: {match['year1']}, School: {match['school1']}")
                print(f"Face 2: {match['face2']}")
                print(f"Year: {match['year2']}, School: {match['school2']}")
            if len(range_matches) > 5:
                print(f"... and {len(range_matches) - 5} more in this range")
    
    print(f"\nTotal unique matches found: {len(unique_matches)}")

def find_matches_for_face(target_filename, min_similarity=70):
    """Find matches for a specific face."""
    app = init_arcface()
    cache = load_cache()
    
    # Get target face encoding
    target_path = os.path.join("static", "extracted_faces", target_filename)
    if not os.path.exists(target_path):
        print(f"Target face not found: {target_filename}")
        return []
        
    target_encoding = get_face_encoding(app, target_path, cache)
    if target_encoding is None:
        print(f"Could not encode target face: {target_filename}")
        return []
    
    # Get all other faces
    conn = sqlite3.connect("faces.db")
    cursor = conn.cursor()
    cursor.execute("SELECT filename, yearbook_year, school_name FROM faces WHERE filename != ?", (target_filename,))
    other_faces = cursor.fetchall()
    conn.close()
    
    matches = []
    for filename, year, school in tqdm(other_faces, desc="Finding matches"):
        path = os.path.join("static", "extracted_faces", filename)
        if not os.path.exists(path):
            continue
            
        encoding = get_face_encoding(app, path, cache)
        if encoding is None:
            continue
            
        similarity = calculate_similarity(target_encoding, encoding)
        if similarity >= min_similarity:
            matches.append({
                'filename': filename,
                'similarity': float(similarity),
                'year': year,
                'school': school
            })
    
    return sorted(matches, key=lambda x: x['similarity'], reverse=True)

if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        print("Starting ArcFace matching with parallel processing...")
        find_matches() 