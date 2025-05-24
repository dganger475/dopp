#!/usr/bin/env python3
"""
Database Fix Script for DoppleGanger

This script fixes inconsistent filenames in the faces database where:
- filename has pattern 'face_XXXXX.jpg'
- image_path contains the actual filename

NO tables will be dropped and NO data will be deleted.
"""

import os
import re
import shutil
import sqlite3
import time
from datetime import datetime

from app_config import DB_PATH

# Configuration
BACKUP_DIR = 'db_backups'

def create_backup(db_path):
    """Create a backup of the database before making changes."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Ensure backup directory exists
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    backup_path = os.path.join(BACKUP_DIR, f"{os.path.basename(db_path)}_{timestamp}.bak")
    
    print(f"Creating backup at: {backup_path}")
    shutil.copy2(db_path, backup_path)
    return backup_path

def fix_filenames():
    """Fix inconsistent filenames in the faces database."""
    # Create backup first
    backup_path = create_backup(DB_PATH)
    
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # First, count how many records need fixing
        cursor.execute("""
            SELECT COUNT(*) 
            FROM faces 
            WHERE filename LIKE 'face_%' 
            AND image_path IS NOT NULL 
            AND image_path != '' 
            AND image_path != filename
        """)
        
        total_to_fix = cursor.fetchone()[0]
        print(f"Found {total_to_fix} records with inconsistent filenames")
        
        if total_to_fix == 0:
            print("No records need fixing. Exiting.")
            return
        
        # Ask for confirmation
        confirm = input(f"Do you want to fix {total_to_fix} records? (y/n): ")
        if confirm.lower() not in ['y', 'yes']:
            print("Operation cancelled. No changes made.")
            return
        
        # Get records that need fixing
        cursor.execute("""
            SELECT id, filename, image_path 
            FROM faces 
            WHERE filename LIKE 'face_%' 
            AND image_path IS NOT NULL 
            AND image_path != '' 
            AND image_path != filename
        """)
        
        fixed_count = 0
        skipped_count = 0
        error_count = 0
        
        # Prepare log file
        log_path = os.path.join(BACKUP_DIR, f"fixed_filenames_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        with open(log_path, 'w') as log_file:
            log_file.write(f"Filename fix log - {datetime.now()}\n")
            log_file.write(f"Database: {DB_PATH}\n")
            log_file.write(f"Backup: {backup_path}\n\n")
            
            for row in cursor.fetchall():
                record_id = row['id']
                old_filename = row['filename']
                image_path = row['image_path']
                
                # Extract just the filename from the image path
                # Handle different path formats
                if '/' in image_path:
                    new_filename = os.path.basename(image_path)
                else:
                    new_filename = image_path
                
                log_message = f"ID {record_id}: {old_filename} -> {new_filename}"
                
                try:
                    # Validate the new filename
                    if not new_filename or len(new_filename) < 5:
                        log_message += " [SKIPPED: Invalid new filename]"
                        log_file.write(log_message + "\n")
                        skipped_count += 1
                        continue
                    
                    # Update the record
                    update_cursor = conn.cursor()
                    update_cursor.execute(
                        "UPDATE faces SET filename = ? WHERE id = ?",
                        (new_filename, record_id)
                    )
                    fixed_count += 1
                    log_file.write(log_message + " [FIXED]\n")
                    
                except Exception as e:
                    error_message = f" [ERROR: {str(e)}]"
                    log_message += error_message
                    log_file.write(log_message + "\n")
                    error_count += 1
        
        # Commit changes
        conn.commit()
        
        print(f"\nDatabase update complete!")
        print(f"Fixed: {fixed_count}")
        print(f"Skipped: {skipped_count}")
        print(f"Errors: {error_count}")
        print(f"Log file: {log_path}")
        
    except Exception as e:
        conn.rollback()
        print(f"Error: {str(e)}")
        print(f"No changes were made. Your database is safe.")
    finally:
        conn.close()

if __name__ == "__main__":
    print("DopplegangerApp Database Filename Fix Tool")
    print("==========================================")
    print("WARNING: This will update filenames in the database.")
    print("A backup will be created before making any changes.")
    print("")
    
    try:
        fix_filenames()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user. No changes made.")
