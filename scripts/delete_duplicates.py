import os
import sqlite3

import face_recognition
from tqdm import tqdm

import numpy as np


def find_and_delete_duplicates():
    """Find and delete duplicate faces based on encoding similarity."""
    conn = sqlite3.connect("faces.db")
    cursor = conn.cursor()
    
    print("\nFetching all faces from database...")
    cursor.execute("""
        SELECT id, filename, image_path, encoding, yearbook_year, school_name, page_number 
        FROM faces 
        WHERE encoding IS NOT NULL
    """)
    faces = cursor.fetchall()
    
    total_faces = len(faces)
    print(f"\nAnalyzing {total_faces} faces for duplicates...")
    
    # Track duplicates
    duplicates = []
    processed = set()
    
    # Compare faces
    for i in tqdm(range(len(faces)), desc="Finding duplicates"):
        if i in processed:
            continue
            
        face1_id, face1_filename, face1_path, face1_encoding, year1, school1, page1 = faces[i]
        encoding1 = np.frombuffer(face1_encoding, dtype=np.float64)
        
        matches = []
        
        # Compare with other faces
        for j in range(i + 1, len(faces)):
            if j in processed:
                continue
                
            face2_id, face2_filename, face2_path, face2_encoding, year2, school2, page2 = faces[j]
            encoding2 = np.frombuffer(face2_encoding, dtype=np.float64)
            
            # Calculate similarity
            distance = face_recognition.face_distance([encoding1], encoding2)[0]
            similarity = (1 - distance) * 100
            
            # If very similar (95% or more), consider it a duplicate
            if similarity >= 95:
                matches.append({
                    'id': face2_id,
                    'filename': face2_filename,
                    'path': face2_path,
                    'similarity': similarity,
                    'year': year2,
                    'school': school2,
                    'page': page2
                })
                processed.add(j)
        
        # If duplicates found, add to list
        if matches:
            duplicates.append({
                'original': {
                    'id': face1_id,
                    'filename': face1_filename,
                    'path': face1_path,
                    'year': year1,
                    'school': school1,
                    'page': page1
                },
                'duplicates': matches
            })
            processed.add(i)
    
    if not duplicates:
        print("\nNo duplicates found!")
        conn.close()
        return
    
    # Print duplicate groups
    print("\nFound Duplicate Groups:")
    print("=" * 80)
    
    total_duplicates = 0
    for group in duplicates:
        print(f"\nOriginal: {group['original']['filename']}")
        print(f"Year: {group['original']['year']}, School: {group['original']['school']}, Page: {group['original']['page']}")
        print("Duplicates:")
        for dup in group['duplicates']:
            print(f"- {dup['filename']} (Similarity: {dup['similarity']:.1f}%)")
            total_duplicates += 1
    
    print("\nSummary:")
    print(f"Total duplicate groups found: {len(duplicates)}")
    print(f"Total duplicate files: {total_duplicates}")
    
    # Ask for confirmation
    response = input("\nDo you want to delete the duplicate files? (yes/no): ")
    
    if response.lower() == 'yes':
        deleted_count = 0
        
        print("\nDeleting duplicates...")
        for group in tqdm(duplicates, desc="Processing groups"):
            for dup in group['duplicates']:
                try:
                    # Delete from database
                    cursor.execute("DELETE FROM faces WHERE id = ?", (dup['id'],))
                    
                    # Delete file
                    if os.path.exists(dup['path']):
                        os.remove(dup['path'])
                        deleted_count += 1
                except Exception as e:
                    print(f"Error deleting {dup['filename']}: {e}")
        
        # Commit changes
        conn.commit()
        
        # Get remaining count
        cursor.execute("SELECT COUNT(*) FROM faces")
        remaining_count = cursor.fetchone()[0]
        
        print("\nDeletion Summary")
        print("=" * 50)
        print(f"Successfully deleted: {deleted_count}")
        print(f"Remaining faces in database: {remaining_count}")
    else:
        print("\nOperation cancelled")
    
    conn.close()

if __name__ == "__main__":
    print("This script will identify and delete duplicate faces from the database.")
    print("Duplicates are determined by 95% or higher similarity in face encodings.")
    print("\nAnalyzing database...")
    
    find_and_delete_duplicates() 