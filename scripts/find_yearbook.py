import sqlite3
import sys
from pathlib import Path


def find_yearbook(face_filename):
    conn = sqlite3.connect('faces.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT pdf_path, school_name, yearbook_year, page_number 
        FROM faces 
        WHERE filename = ?
    """, (face_filename,))
    
    result = cursor.fetchone()
    if result:
        pdf_path, school, year, page = result
        print(f"\nFound yearbook for {face_filename}:")
        print(f"PDF Location: {pdf_path}")
        print(f"School: {school}")
        print(f"Year: {year}")
        print(f"Page: {page}")
        
        if Path(pdf_path).exists():
            print("✓ PDF file exists at this location")
        else:
            print("⚠ PDF file not found at this location!")
    else:
        print(f"No yearbook found for {face_filename}")
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python find_yearbook.py <face_filename>")
        sys.exit(1)
    
    find_yearbook(sys.argv[1]) 