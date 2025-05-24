"""
A dedicated script to show EXACTLY what's happening with the similarity calculations.
This bypasses all caching, routing, and web interfaces to show the raw calculation.
"""
import os
import pickle
import sys

import faiss
from flask import Flask

import numpy as np
from models.face import Face
from utils.db.database import get_db_connection
from utils.faiss_index_manager import faiss_index_manager

# Create a minimal Flask app to load models
app = Flask(__name__)
app.config.from_object('config.config.DevelopmentConfig')

def main():
    print("\n===== FACE SIMILARITY ANALYSIS =====")
    
    # Get the most recently added face to compare against
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT filename FROM faces ORDER BY id DESC LIMIT 1")
    latest_face = c.fetchone()
    reference_filename = latest_face[0] if latest_face else None
    
    if not reference_filename:
        print("No faces found in the database")
        return
        
    print(f"Reference face: {reference_filename}")
    
    # Get the face encoding for the reference face
    reference_face = Face.get_by_filename(reference_filename)
    
    if not reference_face or not reference_face.encoding:
        print("Reference face has no encoding")
        return
        
    # Run FAISS search
    print("\nRunning FAISS search...")
    distances, indices, filenames = faiss_index_manager.search(reference_face.encoding, top_k=10)
    
    print("\n===== RAW DISTANCE VALUES =====")
    print("FAISS L2 distances (lower is more similar):")
    for i, (dist, fname) in enumerate(zip(distances, filenames)):
        if i < 10:  # Show first 10 results
            if fname:
                # Skip self-matches
                if fname == reference_filename:
                    print(f"#{i+1}: {fname} - Distance: {dist:.6f} [SELF MATCH - SKIPPED]")
                    continue
                
                print(f"#{i+1}: {fname} - Distance: {dist:.6f}")
    
    print("\n===== SIMILARITY CALCULATIONS =====")
    
    print("\n1. Direct conversion (similarity = (1 - distance) * 100):")
    for i, (dist, fname) in enumerate(zip(distances, filenames)):
        if i < 10 and fname and fname != reference_filename:
            similarity = (1 - dist) * 100
            print(f"#{i+1}: Distance: {dist:.6f} → Similarity: {similarity:.2f}%")
    
    print("\n2. Fixed scale (threshold = 0.6):")
    threshold = 0.6
    for i, (dist, fname) in enumerate(zip(distances, filenames)):
        if i < 10 and fname and fname != reference_filename:
            similarity = max(0, (1 - (dist / threshold)) * 100)
            print(f"#{i+1}: Distance: {dist:.6f} → Similarity: {similarity:.2f}%")
    
    print("\n3. Min-max normalization (makes best match 100%):")
    # Only show this if there are multiple results
    if len(distances) > 1:
        min_dist = min([d for i, d in enumerate(distances) if filenames[i] != reference_filename])
        max_dist = max([d for i, d in enumerate(distances) if filenames[i] != reference_filename])
        
        if max_dist - min_dist > 0:
            for i, (dist, fname) in enumerate(zip(distances, filenames)):
                if i < 10 and fname and fname != reference_filename:
                    normalized = (dist - min_dist) / (max_dist - min_dist)
                    similarity = (1 - normalized) * 100
                    print(f"#{i+1}: Distance: {dist:.6f} → Normalized: {normalized:.6f} → Similarity: {similarity:.2f}%")
    
    print("\n===== CALCULATION COMPARISON =====")
    print("Look at the 'Fixed scale' calculation - this is likely what you want!")
    print("It gives absolute similarity scores where 0.0 distance = 100%")
    print("and distances >= 0.6 = 0% similarity.")
    
if __name__ == "__main__":
    main()
