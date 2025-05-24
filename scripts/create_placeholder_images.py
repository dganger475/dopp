"""
Generate placeholder images for database entries.
This script creates placeholder images for database entries with missing files.
"""
import os
import random
import sqlite3

from PIL import Image, ImageDraw, ImageFont


def get_db_path(db_name):
    """Get the path to the database file."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, f'{db_name}.db')

def get_static_path(subdir=''):
    """Get the path to the static directory."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(current_dir, 'static', subdir)

def generate_placeholder_image(filename, text=None, size=(200, 200)):
    """Generate a placeholder image with random color and optional text."""
    # Create output directory if it doesn't exist
    output_dir = get_static_path('faces')
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, filename)
    
    # Skip if file already exists
    if os.path.exists(output_path):
        return output_path
    
    # Random colorful background
    colors = [
        (78, 115, 223),   # Blue
        (54, 185, 204),   # Cyan
        (246, 194, 62),   # Yellow
        (231, 74, 59),    # Red
        (43, 167, 120),   # Green
        (111, 66, 193),   # Purple
        (253, 126, 20)    # Orange
    ]
    color = random.choice(colors)
    
    img = Image.new('RGB', size, color=color)
    draw = ImageDraw.Draw(img)
    
    # Add text if provided
    if text:
        try:
            # Try to use Arial font
            font = ImageFont.truetype('arial.ttf', 32)
        except IOError:
            # Fallback to default font
            font = ImageFont.load_default()
        
        # Center text
        draw.text((size[0]//2, size[1]//2), text, fill='white', anchor='mm', font=font)
    
    # Save the image
    img.save(output_path)
    print(f"Created placeholder image: {output_path}")
    
    return output_path

def create_default_profile():
    """Create a default profile image."""
    output_path = os.path.join(get_static_path(), 'default_profile.png')
    
    if not os.path.exists(output_path):
        img = Image.new('RGB', (200, 200), color=(78, 115, 223))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype('arial.ttf', 80)
        except IOError:
            font = ImageFont.load_default()
            
        # Draw a question mark in the center
        draw.text((100, 100), '?', fill='white', anchor='mm', font=font)
        
        img.save(output_path)
        print(f"Created default profile image: {output_path}")
    
    return output_path

def generate_placeholders_for_db_entries(limit=50):
    """Generate placeholder images for database entries."""
    # Create default profile image
    create_default_profile()
    
    # Connect to faces database
    faces_db_path = get_db_path('faces')
    
    if not os.path.exists(faces_db_path):
        print(f"Faces database not found at {faces_db_path}")
        return
    
    try:
        conn = sqlite3.connect(faces_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get entries from the database
        cursor.execute(f"SELECT * FROM faces ORDER BY RANDOM() LIMIT {limit}")
        entries = cursor.fetchall()
        
        if not entries:
            print("No entries found in the database")
            return
        
        print(f"Generating placeholders for {len(entries)} entries...")
        
        for entry in entries:
            entry_dict = dict(entry)
            filename = entry_dict.get('filename')
            
            if not filename:
                continue
            
            # Check if the file exists in the static/faces directory
            file_path = os.path.join(get_static_path('faces'), filename)
            
            if not os.path.exists(file_path):
                # Generate placeholder with school name or year as text
                text = entry_dict.get('school_name') or entry_dict.get('yearbook_year') or str(entry_dict.get('id'))
                if isinstance(text, (int, float)):
                    text = str(text)
                generate_placeholder_image(filename, text)
        
        print("Placeholder generation complete!")
        
    except Exception as e:
        print(f"Error generating placeholders: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def generate_placeholders_for_user_matches():
    """Generate placeholder images for user matches."""
    # Connect to users database
    users_db_path = get_db_path('users')
    
    if not os.path.exists(users_db_path):
        print(f"Users database not found at {users_db_path}")
        return
    
    try:
        conn = sqlite3.connect(users_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if user_matches table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_matches'")
        if not cursor.fetchone():
            print("user_matches table not found")
            return
        
        # Get matches from the database
        cursor.execute("SELECT * FROM user_matches")
        matches = cursor.fetchall()
        
        if not matches:
            print("No matches found in the database")
            return
        
        print(f"Generating placeholders for {len(matches)} user matches...")
        
        for match in matches:
            match_dict = dict(match)
            filename = match_dict.get('match_filename')
            
            if not filename:
                continue
            
            # Check if the file exists in the static/faces directory
            file_path = os.path.join(get_static_path('faces'), filename)
            
            if not os.path.exists(file_path):
                # Generate placeholder with user_id as text
                text = f"Match {match_dict.get('id')}"
                generate_placeholder_image(filename, text)
        
        print("User match placeholder generation complete!")
        
    except Exception as e:
        print(f"Error generating user match placeholders: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def generate_placeholders_for_claimed_profiles():
    """Generate placeholder images for claimed profiles."""
    # Connect to users database
    users_db_path = get_db_path('users')
    
    if not os.path.exists(users_db_path):
        print(f"Users database not found at {users_db_path}")
        return
    
    try:
        conn = sqlite3.connect(users_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if claimed_profiles table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='claimed_profiles'")
        if not cursor.fetchone():
            print("claimed_profiles table not found")
            return
        
        # Get profiles from the database
        cursor.execute("SELECT * FROM claimed_profiles")
        profiles = cursor.fetchall()
        
        if not profiles:
            print("No claimed profiles found in the database")
            return
        
        print(f"Generating placeholders for {len(profiles)} claimed profiles...")
        
        for profile in profiles:
            profile_dict = dict(profile)
            filename = profile_dict.get('face_filename')
            
            if not filename:
                continue
            
            # Check if the file exists in the static/faces directory
            file_path = os.path.join(get_static_path('faces'), filename)
            
            if not os.path.exists(file_path):
                # Generate placeholder with relationship as text
                text = profile_dict.get('relationship') or f"Profile {profile_dict.get('id')}"
                generate_placeholder_image(filename, text)
        
        print("Claimed profile placeholder generation complete!")
        
    except Exception as e:
        print(f"Error generating claimed profile placeholders: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Create default profile image
    create_default_profile()
    
    # Generate placeholders for database entries
    generate_placeholders_for_db_entries(50)
    
    # Generate placeholders for user matches
    generate_placeholders_for_user_matches()
    
    # Generate placeholders for claimed profiles
    generate_placeholders_for_claimed_profiles()
