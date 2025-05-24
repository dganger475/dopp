import os
import shutil


def clean_pycache(directory):
    for root, dirs, files in os.walk(directory):
        # Remove __pycache__ directories
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            print(f"Removing {pycache_path}")
            shutil.rmtree(pycache_path, ignore_errors=True)
        
        # Remove .pyc, .pyo, and .pyd files
        for file in files:
            if file.endswith(('.pyc', '.pyo', '.pyd')):
                file_path = os.path.join(root, file)
                print(f"Removing {file_path}")
                try:
                    os.remove(file_path)
                except OSError:
                    pass

if __name__ == "__main__":
    project_dir = os.path.dirname(os.path.abspath(__file__))
    print("Cleaning Python cache files...")
    clean_pycache(project_dir)
    print("Cache cleaning complete.")
    
    # Also clean the DopplegangerApp-clean directory if it exists
    clean_dir = os.path.join(project_dir, 'DopplegangerApp-clean')
    if os.path.exists(clean_dir):
        print("\nCleaning DopplegangerApp-clean directory...")
        clean_pycache(clean_dir)
        print("Cache cleaning complete for DopplegangerApp-clean.")
