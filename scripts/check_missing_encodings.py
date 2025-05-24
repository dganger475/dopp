import sqlite3

DATABASE_FILE = r"C:\Users\1439\Documents\DopplegangerApp\faces.db"

def check_missing_encodings():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT filename, image_path FROM faces WHERE encoding IS NULL OR encoding = ''")
    missing_encodings = cursor.fetchall()
    
    conn.close()
    
    print(f"🔹 Faces with missing encodings: {len(missing_encodings)}")
    
    # Print first 10 missing encodings for review
    for img in missing_encodings[:10]:
        print(f"⚠️ Missing Encoding: {img[0]} - {img[1]}")

    return missing_encodings

missing_encodings = check_missing_encodings()
