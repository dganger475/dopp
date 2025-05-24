import os
import sqlite3
import sys


def delete_files_and_encodings(images_to_delete, faces_dir, db_name):
    """
    Delete specified image files and their associated encodings from the database
    
    Args:
        images_to_delete (list): List of image filenames to delete
        faces_dir (str): Directory containing the face images
        db_name (str): Name of the SQLite database file
    """
    # Get the current directory (where this script is running)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, db_name)
    
    # Connect to the database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print(f"Successfully connected to database at {db_path}")
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return

    # Track successful and failed operations
    deleted_files = []
    failed_files = []
    deleted_db_entries = []
    failed_db_entries = []
    
    # Process each image
    for image in images_to_delete:
        # Delete the file if it exists
        file_path = os.path.join(faces_dir, image)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_files.append(image)
                print(f"Deleted file: {file_path}")
            else:
                failed_files.append(image)
                print(f"File not found: {file_path}")
        except Exception as e:
            failed_files.append(image)
            print(f"Error deleting file {file_path}: {e}")
        
        # Delete the corresponding database entry
        try:
            # Assuming your database has a table named 'faces' with a 'filename' column
            # Adjust the table and column names as needed
            cursor.execute("DELETE FROM faces WHERE filename = ?", (image,))
            if cursor.rowcount > 0:
                deleted_db_entries.append(image)
                print(f"Deleted database entry for: {image}")
            else:
                failed_db_entries.append(image)
                print(f"No database entry found for: {image}")
        except sqlite3.Error as e:
            failed_db_entries.append(image)
            print(f"Database error for {image}: {e}")
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    # Summary
    print("\n--- Summary ---")
    print(f"Files successfully deleted: {len(deleted_files)}")
    print(f"Files not found or failed to delete: {len(failed_files)}")
    print(f"Database entries successfully deleted: {len(deleted_db_entries)}")
    print(f"Database entries not found or failed to delete: {len(failed_db_entries)}")

def main():
    # Set paths relative to the current script location
    faces_dir = r"static\extracted_faces"
    db_name = "faces.db"
    
    # List of images to delete (all files)
    images_to_delete = [
        # First batch
        "2014_Davidson_College_page_92_face_13.jpg",
        "Cambell_Univ_2011_Buies_Creek,_NC_page_257_face_3_w125h125.jpg",
        "2013_Methodist_Univ_page_76_face_2.jpg",
        "2014_Elon_Univ_page_51_face_5.jpg",
        "2014_St_Andrews_Univ_page_14_face_18.jpg",
        "2013_Davidson_College_page_87_face_22.jpg",
        "2014_St_Andrews_Univ_page_60_face_2.jpg", 
        "2014_Davidson_College_page_65_face_1.jpg",
        "2011_Leinor_Ryne_Univ_page_164_face_30.jpg",
        "LSU_2012_page_71_face_1.jpg",
        
        # Second batch
        "Mount_Saint_Joseph_Cincinatti_OH_2012_page_25_face_13.jpg",
        "2012_Univ_Mississippi_page_257_face_14.jpg",
        "2010William_Carey_Univ_Hattiesburg_MS_page_81_face_6.jpg",
        "2012_NorthCarolina_School_ScienceMathematics_page_46_face_2.jpg",
        "2014_Davidson_College_page_83_face_12.jpg",
        
        # Third batch
        "2011_Leinor_Ryne_Univ_page_179_face_25.jpg",
        "2012_NorthCarolina_School_ScienceMathematics_page_107_face_1.jpg",
        "2011_Leinor_Ryne_Univ_page_160_face_40.jpg",
        
        # Fourth batch
        "2014_Davidson_College_page_76_face_22.jpg",
        "Cambell_Univ_2011_Buies_Creek,_NC_page_303_face_4_w100h100.jpg",
        "Ouachita_Univ_2010_People_Arkadelphia_AR_page_9_face_31.jpg",
        "2012_fayettevillie_univ_page_80_face_4.jpg"
    ]
    
    # Confirm deletion
    print(f"This will delete {len(images_to_delete)} files and their database entries.")
    confirm = input("Continue? (y/n): ")
    
    if confirm.lower() == 'y':
        delete_files_and_encodings(images_to_delete, faces_dir, db_name)
    else:
        print("Operation cancelled.")

if __name__ == "__main__":
    main()