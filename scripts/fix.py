import os

import cv2
from PIL import Image

# Set your folder path
FOLDER_PATH = r"C:\Users\1439\Documents\DopplegangerApp\static\extracted_faces"

# Ensure the folder exists
if not os.path.exists(FOLDER_PATH):
    print("Folder path does not exist!")
    exit()

# Backup check
BACKUP_FOLDER = os.path.join(FOLDER_PATH, "backup")
if not os.path.exists(BACKUP_FOLDER):
    os.makedirs(BACKUP_FOLDER)

# Supported image formats
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp")

def resize_image(image_path, output_size=(300, 300)):
    """Resizes the image to the specified size."""
    try:
        img = Image.open(image_path)
        img = img.resize(output_size, Image.LANCZOS)  # LANCZOS gives high-quality downsampling
        img.save(image_path)  # Overwrite with resized image
        print(f"Resized: {image_path}")
    except Exception as e:
        print(f"Error processing {image_path}: {e}")

def process_images(folder_path):
    """Processes all images in the folder, resizing them to 300x300."""
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        
        if file_name.lower().endswith(IMAGE_EXTENSIONS):
            backup_path = os.path.join(BACKUP_FOLDER, file_name)
            
            # Backup original if not already backed up
            if not os.path.exists(backup_path):
                try:
                    Image.open(file_path).save(backup_path)
                    print(f"Backup created: {backup_path}")
                except Exception as e:
                    print(f"Failed to backup {file_name}: {e}")

            # Resize the image
            resize_image(file_path)

if __name__ == "__main__":
    process_images(FOLDER_PATH)
    print("Processing complete. All images are now 300x300.")
