#!/usr/bin/env python
"""
Repository organization script.
This script helps organize the repository by moving utility scripts to the scripts directory.
"""

import logging
import os
import re
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Root directory of the project
ROOT_DIR = Path(__file__).parent.parent.absolute()

# Scripts directory
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")

# Patterns for script files to move
SCRIPT_PATTERNS = [
    r"^(build|rebuild|extract|cleanup|delete|fix|update|encode|find).*\.py$",
    r"^check.*\.py$",
    r"^create.*\.py$",
    r"^.*_test\.py$",
    r"^test_.*\.py$",
    r"^.*_script\.py$",
]

# Files to exclude (core application files)
EXCLUDE_FILES = [
    "app.py",
    "wsgi.py",
    "config.py",
    "manage.py",
    "run.py",
    "database.py",
    "models.py",
    "__init__.py",
]

# Directories to exclude
EXCLUDE_DIRS = [
    "venv",
    "env",
    ".git",
    ".github",
    "migrations",
    "static",
    "templates",
    "models",
    "routes",
    "utils",
    "scripts",
    "__pycache__",
]

def is_script_file(filename):
    """Check if a file is a script file based on patterns."""
    for pattern in SCRIPT_PATTERNS:
        if re.match(pattern, filename):
            return True
    return False

def should_move_file(filepath):
    """Check if a file should be moved to the scripts directory."""
    filename = os.path.basename(filepath)
    
    # Skip excluded files
    if filename in EXCLUDE_FILES:
        return False
    
    # Skip files in excluded directories
    for exclude_dir in EXCLUDE_DIRS:
        if exclude_dir in filepath.split(os.sep):
            return False
    
    # Check if it's a Python file
    if not filename.endswith(".py"):
        return False
    
    # Check if it matches script patterns
    return is_script_file(filename)

def organize_scripts():
    """Organize script files by moving them to the scripts directory."""
    # Ensure scripts directory exists
    os.makedirs(SCRIPTS_DIR, exist_ok=True)
    
    # Get all Python files in the root directory
    python_files = []
    for root, dirs, files in os.walk(ROOT_DIR):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, ROOT_DIR)
                
                # Skip files in subdirectories
                if os.sep in rel_path:
                    continue
                
                python_files.append(filepath)
    
    # Move script files to the scripts directory
    moved_files = []
    for filepath in python_files:
        if should_move_file(filepath):
            filename = os.path.basename(filepath)
            dest_path = os.path.join(SCRIPTS_DIR, filename)
            
            # Skip if file already exists in scripts directory
            if os.path.exists(dest_path):
                logger.info(f"File already exists in scripts directory: {filename}")
                continue
            
            try:
                shutil.copy2(filepath, dest_path)
                logger.info(f"Moved {filename} to scripts directory")
                moved_files.append(filename)
            except Exception as e:
                logger.error(f"Error moving {filename}: {e}")
    
    logger.info(f"Moved {len(moved_files)} files to scripts directory")
    return moved_files

if __name__ == "__main__":
    organize_scripts()
