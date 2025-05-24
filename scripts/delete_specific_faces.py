import os
import sqlite3
import urllib.parse

# List of faces to delete
faces_to_delete = [
    # First batch
    "BULKELEY HIGH SCHOOL ALUMNI ASSOCIATION_2007_page_36_face_6.jpg",
    "Unknown School_2007_page_300_face_12.jpg",
    "Unknown School_2006_page_294_face_15.jpg",
    "Unknown School_2007_page_270_face_16.jpg",
    "Unknown School_2006_page_285_face_8.jpg",
    "Unknown School_2006_page_287_face_13.jpg",
    "Unknown School_2006_page_312_face_9.jpg",
    "2013 Holmes Community College_2013_page_32_face_4.jpg",
    "Taylor University_2010_page_152_face_18.jpg",
    
    # Second batch
    "Unknown School_2005_page_212_face_1.jpg",
    "Taylor University_2010_page_145_face_1.jpg",
    "Taylor University_2010_page_93_face_1.jpg",
    "Unknown School_2006_page_283_face_4.jpg",
    "Alameda Unified School District_2005_page_110_face_7.jpg",
    "Unknown School_2006_page_283_face_12.jpg",
    "Alameda Unified School District_2005_page_139_face_18.jpg",
    "Taylor University_2006_page_172_face_21.jpg",
    "Alameda Unified School District_2011_page_265_face_6.jpg",
    "2011 Holmes Community College_2011_page_149_face_14.jpg"
]

def delete_faces():
    """Delete specified faces from both filesystem and database."""
    # Connect to database
    conn = sqlite3.connect("faces.db")
    cursor = conn.cursor()
    
    deleted_count = 0
    failed_count = 0
    
    print("\nStarting deletion process...")
    print("=" * 50)
    
    for face in faces_to_delete:
        try:
            # URL decode the filename
            decoded_filename = urllib.parse.unquote(face)
            
            # Get the file path
            file_path = os.path.join("static", "extracted_faces", decoded_filename)
            
            # Delete from database first
            cursor.execute("DELETE FROM faces WHERE filename = ?", (decoded_filename,))
            
            # Delete file if it exists
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"✅ Successfully deleted: {decoded_filename}")
                deleted_count += 1
            else:
                print(f"⚠️ File not found: {decoded_filename}")
                failed_count += 1
                
        except Exception as e:
            print(f"❌ Error deleting {face}: {e}")
            failed_count += 1
    
    # Commit database changes
    conn.commit()
    
    # Get remaining face count
    cursor.execute("SELECT COUNT(*) FROM faces")
    remaining_count = cursor.fetchone()[0]
    
    # Close database connection
    conn.close()
    
    print("\nDeletion Summary")
    print("=" * 50)
    print(f"Successfully deleted: {deleted_count}")
    print(f"Failed to delete: {failed_count}")
    print(f"Remaining faces in database: {remaining_count}")

if __name__ == "__main__":
    print("This script will delete specific faces from both the filesystem and database.")
    response = input("Do you want to proceed? (yes/no): ")
    
    if response.lower() == 'yes':
        delete_faces()
    else:
        print("Operation cancelled") 