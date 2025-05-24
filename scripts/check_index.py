import os
import pickle

import faiss

# Check FAISS index
try:
    print("Checking FAISS index...")
    index = faiss.read_index('faces.index')
    print(f"Number of vectors in FAISS index: {index.ntotal}")
except Exception as e:
    print(f"Error reading FAISS index: {e}")

# Check filename mapping
try:
    print("\nChecking filename mapping...")
    if os.path.exists('faces_filenames.pkl'):
        with open('faces_filenames.pkl', 'rb') as f:
            filenames = pickle.load(f)
            print(f"Number of filenames in mapping: {len(filenames)}")
            print(f"First 5 filenames: {filenames[:5]}")
    else:
        print("Filename mapping file not found!")
except Exception as e:
    print(f"Error reading filename mapping: {e}")

# Check database
try:
    print("\nChecking database...")
    import sqlite3
    conn = sqlite3.connect('faces.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM faces")
    count = cursor.fetchone()[0]
    print(f"Number of entries in faces.db: {count}")
    
    cursor.execute("SELECT COUNT(*) FROM faces WHERE encoding IS NOT NULL")
    count = cursor.fetchone()[0]
    print(f"Number of entries with encodings: {count}")
    
    conn.close()
except Exception as e:
    print(f"Error checking database: {e}")
