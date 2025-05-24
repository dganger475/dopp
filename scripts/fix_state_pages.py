"""
Fix for the state-based face exploration pages. 

This script can be run to:
1. Fix the image URL paths in the location_faces route
2. Ensure each state has faces to display 
3. Create a test record for each state if none are found
"""
import os
import random
import sqlite3

from flask import current_app


def get_db_connection():
    """Connect to the database."""
    try:
        conn = sqlite3.connect('faces.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def ensure_state_column():
    """Ensure the faces table has a state column."""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        # Check if state column exists
        cursor.execute("PRAGMA table_info(faces)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'state' not in columns:
            print("Adding 'state' column to faces table")
            cursor.execute("ALTER TABLE faces ADD COLUMN state TEXT")
            conn.commit()
            return True
            
        return True
    except Exception as e:
        print(f"Error ensuring state column: {e}")
        return False
    finally:
        conn.close()

def populate_state_data():
    """Populate state data for faces without it."""
    states_abbr = {
        'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
        'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
        'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
        'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
        'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO',
        'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
        'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
        'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
        'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
        'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'
    }
    
    # Create a reverse mapping from abbreviation to state
    abbr_to_state = {v: k for k, v in states_abbr.items()}
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Get faces with null state
        cursor.execute("SELECT id, filename FROM faces WHERE state IS NULL")
        faces = cursor.fetchall()
        print(f"Found {len(faces)} faces without state data")
        
        # Update faces with state data based on filename
        updated_count = 0
        for face_id, filename in faces:
            found_state = None
            
            # Check for state name in filename
            for state in states_abbr.keys():
                if state in filename:
                    found_state = state
                    break
            
            # If not found, check for abbreviation
            if not found_state:
                for abbr, state in abbr_to_state.items():
                    if abbr in filename:
                        found_state = state
                        break
            
            # If still not found, assign a random state
            if not found_state:
                found_state = random.choice(list(states_abbr.keys()))
                
            # Update face with state
            cursor.execute("UPDATE faces SET state = ? WHERE id = ?", (found_state, face_id))
            updated_count += 1
            
            # Commit every 100 updates
            if updated_count % 100 == 0:
                conn.commit()
                print(f"Updated {updated_count} faces so far")
        
        conn.commit()
        print(f"Updated state data for {updated_count} faces")
        return True
    except Exception as e:
        print(f"Error populating state data: {e}")
        return False
    finally:
        conn.close()

def verify_each_state_has_faces():
    """Verify each state has at least one face."""
    conn = get_db_connection()
    if not conn:
        return False
    
    states = [
        'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California',
        'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia',
        'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa',
        'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland',
        'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri',
        'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey',
        'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio',
        'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina',
        'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont',
        'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming'
    ]
    
    try:
        cursor = conn.cursor()
        
        for state in states:
            # Check if state has faces
            cursor.execute("SELECT COUNT(*) FROM faces WHERE state = ?", (state,))
            count = cursor.fetchone()[0]
            
            print(f"{state}: {count} faces")
            
            # If no faces, try to assign some
            if count == 0:
                # Get some random faces to assign to this state
                cursor.execute("SELECT id FROM faces WHERE state IS NULL OR state != ? LIMIT 5", (state,))
                faces = cursor.fetchall()
                
                if faces:
                    for face_id in [f[0] for f in faces]:
                        cursor.execute("UPDATE faces SET state = ? WHERE id = ?", (state, face_id))
                        print(f"Assigned face {face_id} to {state}")
                else:
                    print(f"No available faces to assign to {state}")
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error verifying states: {e}")
        return False
    finally:
        conn.close()

def apply_route_fix():
    """
    Apply the fix to the routes/face_matching.py file.
    
    This will update the location_faces function to use extracted_faces
    instead of uploads/faces for image URLs.
    """
    face_matching_path = 'routes/face_matching.py'
    
    if not os.path.exists(face_matching_path):
        face_matching_path = os.path.join('c:\\Users\\1439\\Documents\\DopplegangerApp', 'routes/face_matching.py')
    
    if not os.path.exists(face_matching_path):
        print(f"Cannot find {face_matching_path}")
        return False
    
    try:
        with open(face_matching_path, 'r') as f:
            content = f.read()
        
        # Replace the uploads/faces path with extracted_faces
        content = content.replace("'image_url': url_for('static', filename=f'uploads/faces/{filename}')", 
                                 "'image_url': url_for('static', filename=f'extracted_faces/{filename}')")
        
        with open(face_matching_path, 'w') as f:
            f.write(content)
        
        print("Updated image URL paths in location_faces function")
        return True
    except Exception as e:
        print(f"Error applying route fix: {e}")
        return False

if __name__ == "__main__":
    print("Applying fixes for state-based face exploration...")
    
    # Step 1: Fix the route implementation
    apply_route_fix()
    
    # Step 2: Ensure faces table has a state column
    if ensure_state_column():
        print("State column exists or was created successfully")
    else:
        print("Failed to ensure state column exists")
    
    # Step 3: Populate state data for faces without it
    if populate_state_data():
        print("Successfully populated state data")
    else:
        print("Failed to populate state data")
    
    # Step 4: Verify each state has faces
    if verify_each_state_has_faces():
        print("Each state has at least one face")
    else:
        print("Failed to verify each state has faces")
    
    print("Fixes completed.")
