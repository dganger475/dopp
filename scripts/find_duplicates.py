import os
import shutil
import sqlite3

import face_recognition
from PIL import Image

import numpy as np


def get_db_connection():
    """Establish a connection to the SQLite database."""
    try:
        conn = sqlite3.connect("faces.db")
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def find_similar_pairs():
    """Find pairs of faces with 75%+ similarity from different yearbooks."""
    conn = get_db_connection()
    if not conn:
        return
    
    cursor = conn.cursor()
    
    # Get all faces with their encodings and metadata
    cursor.execute("""
        SELECT filename, encoding, yearbook_year, school_name, page_number
        FROM faces 
        WHERE encoding IS NOT NULL
    """)
    faces = cursor.fetchall()
    conn.close()
    
    # Create output directory for matched pairs
    output_dir = "similar_faces"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a log file for matches
    with open("similar_faces/matches.txt", "w") as log_file:
        match_count = 0
        
        print("🔍 Searching for similar faces...")
        total_faces = len(faces)
        
        # Compare each face with every other face
        for i in range(total_faces):
            face1 = faces[i]
            encoding1 = np.frombuffer(face1['encoding'], dtype=np.float64)
            year1 = face1['yearbook_year']
            
            # Show progress
            print(f"\rProcessing face {i+1}/{total_faces}...", end="")
            
            for j in range(i + 1, total_faces):
                face2 = faces[j]
                year2 = face2['yearbook_year']
                
                # Only compare faces from different yearbooks
                if year1 != year2:
                    encoding2 = np.frombuffer(face2['encoding'], dtype=np.float64)
                    
                    # Calculate similarity
                    distance = face_recognition.face_distance([encoding1], encoding2)[0]
                    similarity = round((1 - distance) * 100, 1)
                    
                    # If similarity is 75% or higher
                    if similarity >= 75:
                        match_count += 1
                        pair_dir = os.path.join(output_dir, f"match_{match_count}")
                        os.makedirs(pair_dir, exist_ok=True)
                        
                        # Copy the matched images
                        for idx, face in enumerate([face1, face2]):
                            src_path = os.path.join("static/extracted_faces", face['filename'])
                            if os.path.exists(src_path):
                                dst_path = os.path.join(pair_dir, f"face_{idx+1}.jpg")
                                shutil.copy2(src_path, dst_path)
                        
                        # Log the match details
                        log_file.write(f"\nMatch {match_count} - Similarity: {similarity}%\n")
                        log_file.write(f"Face 1: {face1['filename']}\n")
                        log_file.write(f"  Year: {face1['yearbook_year']}\n")
                        log_file.write(f"  School: {face1['school_name']}\n")
                        log_file.write(f"  Page: {face1['page_number']}\n")
                        log_file.write(f"Face 2: {face2['filename']}\n")
                        log_file.write(f"  Year: {face2['yearbook_year']}\n")
                        log_file.write(f"  School: {face2['school_name']}\n")
                        log_file.write(f"  Page: {face2['page_number']}\n")
                        log_file.write("-" * 50 + "\n")
                        
                        print(f"\n✨ Found match {match_count}! Similarity: {similarity}%")
                        print(f"Between {year1} and {year2}")
    
    print(f"\n\n✅ Search complete!")
    print(f"Found {match_count} pairs of similar faces")
    print(f"Results saved in the '{output_dir}' folder")
    print(f"Detailed matches logged in '{output_dir}/matches.txt'")

if __name__ == "__main__":
    find_similar_pairs() 