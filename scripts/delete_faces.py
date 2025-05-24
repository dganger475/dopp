import logging
import os
import sqlite3

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# List of faces to delete
faces_to_delete = [
    "calyx2007wash_page_302_face_3.jpg",
    "rayderyearbookch2007char_page_109_face_14.jpg",
    "aesc06drex_page_120_face_5.jpg"
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
            # Get the file path
            file_path = os.path.join("static", "extracted_faces", face)
            
            # Delete from database first
            cursor.execute("DELETE FROM faces WHERE filename = ?", (face,))
            
            # Delete file if it exists
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"✅ Successfully deleted: {face}")
                deleted_count += 1
            else:
                print(f"⚠️ File not found: {face}")
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
    print("This script will delete the specified faces from both the filesystem and database.")
    response = input("Do you want to proceed? (yes/no): ")
    
    if response.lower() == 'yes':
        delete_faces()
    else:
        print("Operation cancelled") 