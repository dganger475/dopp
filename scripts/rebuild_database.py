import concurrent.futures
import logging
import multiprocessing
import os
import sqlite3
import time

import face_recognition
from PIL import Image
from tqdm import tqdm

import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_image_batch(args):
    """Process a batch of images"""
    filenames, faces_dir = args
    results = []
    
    for filename in filenames:
        try:
            image_path = os.path.join(faces_dir, filename)
            
            # Load image using face_recognition directly (much faster)
            face_array = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(face_array, num_jitters=0, model='small')
            
            if encodings:
                # Extract metadata from filename
                parts = filename.split('_')
                year = "Unknown"
                school = "Unknown"
                page = 0
                
                if len(parts) > 2:
                    year_match = next((part for part in parts if part.isdigit() and len(part) == 4), None)
                    if year_match:
                        year = year_match
                    school = parts[0]
                    page_parts = [p for p in parts if 'page' in p.lower()]
                    if page_parts:
                        try:
                            page = int(''.join(filter(str.isdigit, page_parts[0])))
                        except:
                            pass
                
                results.append({
                    'filename': filename,
                    'image_path': image_path,
                    'encoding': encodings[0].tobytes(),
                    'year': year,
                    'school': school,
                    'page': page
                })
                
        except Exception as e:
            logging.error(f"Error processing {filename}: {e}")
            continue
            
    return len(filenames), results

def rebuild_database():
    """Rebuild database from existing face images"""
    start_time = time.time()
    try:
        conn = sqlite3.connect('faces.db')
        cursor = conn.cursor()
        
        faces_dir = os.path.join('static', 'extracted_faces')
        image_files = [f for f in os.listdir(faces_dir) 
                      if f.endswith(('.jpg', '.jpeg', '.png')) and not f.startswith('display_')]
        
        total_images = len(image_files)
        logging.info(f"Found {total_images} total face images")
        
        cursor.execute("SELECT filename FROM faces")
        existing_files = {row[0] for row in cursor.fetchall()}
        logging.info(f"Found {len(existing_files)} existing database entries")
        
        image_files = [f for f in image_files if f not in existing_files]
        to_process = len(image_files)
        logging.info(f"Need to process {to_process} new images")
        
        if to_process == 0:
            logging.info("No new images to process!")
            return
        
        # Smaller batch size for more frequent updates
        batch_size = 20
        batches = [image_files[i:i + batch_size] for i in range(0, len(image_files), batch_size)]
        
        num_cores = multiprocessing.cpu_count()
        logging.info(f"Using {num_cores} CPU cores with {len(batches)} batches")
        
        successful = 0
        all_results = []
        
        with tqdm(total=to_process, desc="Processing faces", unit="faces") as pbar:
            with concurrent.futures.ProcessPoolExecutor(max_workers=num_cores) as executor:
                # Submit initial batch of tasks
                futures = {}
                for batch in batches[:num_cores*2]:  # Start with 2 batches per core
                    future = executor.submit(process_image_batch, (batch, faces_dir))
                    futures[future] = len(batch)
                
                # Process remaining batches as they complete
                batch_index = num_cores*2
                while futures:
                    done, _ = concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_COMPLETED)
                    
                    for future in done:
                        processed_count, batch_results = future.result()
                        all_results.extend(batch_results)
                        successful += len(batch_results)
                        pbar.update(processed_count)
                        
                        # Remove completed future
                        del futures[future]
                        
                        # Submit next batch if available
                        if batch_index < len(batches):
                            new_future = executor.submit(process_image_batch, (batches[batch_index], faces_dir))
                            futures[new_future] = len(batches[batch_index])
                            batch_index += 1
        
        if all_results:
            logging.info(f"Successfully processed {successful} faces")
            
            # Insert with progress bar
            with tqdm(total=len(all_results), desc="Inserting into database", unit="faces") as pbar:
                batch_size = 1000
                for i in range(0, len(all_results), batch_size):
                    batch = all_results[i:i + batch_size]
                    cursor.executemany("""
                        INSERT INTO faces (filename, image_path, encoding, yearbook_year, school_name, page_number)
                        VALUES (:filename, :image_path, :encoding, :year, :school, :page)
                    """, batch)
                    conn.commit()
                    pbar.update(len(batch))
        
        cursor.execute("SELECT COUNT(*) FROM faces")
        total = cursor.fetchone()[0]
        
        elapsed = time.time() - start_time
        logging.info("\nRecovery Summary:")
        logging.info(f"- Total images found: {total_images}")
        logging.info(f"- Previously processed: {len(existing_files)}")
        logging.info(f"- Newly processed: {successful}")
        logging.info(f"- Failed to process: {to_process - successful}")
        logging.info(f"- Total time: {elapsed:.1f} seconds")
        logging.info(f"- Processing rate: {successful/elapsed:.1f} faces/second")
        logging.info(f"- Final database count: {total} entries")
        
    except Exception as e:
        logging.error(f"Error during recovery: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    rebuild_database() 