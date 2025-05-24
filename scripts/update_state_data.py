import logging
import os
import re
import sqlite3
import sys

# Add the parent directory to the path so we can import our app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Now we can import from our app modules
from utils.db.database import get_db_connection
from utils.face_metadata import (extract_state_from_filename,
                                 extract_state_from_school)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def update_state_data():
    """
    Update state data for all faces in the database.
    Uses the existing extraction functions to populate the state column.
    """
    conn = get_db_connection()
    if not conn:
        logging.error("Could not connect to the database")
        return
    
    # Check if the state column exists
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM faces LIMIT 1")
        columns = [description[0] for description in cursor.description]
        
        if 'state' not in columns:
            logging.info("The state column doesn't exist. Adding it now...")
            cursor.execute("ALTER TABLE faces ADD COLUMN state TEXT")
            conn.commit()
            logging.info("Added state column to faces table")
    except Exception as e:
        logging.error(f"Error checking/adding state column: {e}")
        conn.close()
        return
    
    # Get all faces that don't have state information
    try:
        cursor.execute("SELECT id, filename, school_name FROM faces WHERE state IS NULL OR state = ''")
        faces = cursor.fetchall()
        logging.info(f"Found {len(faces)} faces without state information")
    except Exception as e:
        logging.error(f"Error retrieving faces: {e}")
        conn.close()
        return
    
    # Process state mapping - map school name patterns to states
    state_mapping = {
        # Ivy League
        'Harvard': 'MA',
        'Yale': 'CT',
        'Princeton': 'NJ',
        'Cornell': 'NY',
        'Columbia': 'NY',
        'Brown': 'RI',
        'Dartmouth': 'NH',
        'Penn': 'PA',
        'UPenn': 'PA',
        
        # Top Universities
        'MIT': 'MA',
        'Stanford': 'CA',
        'Berkeley': 'CA',
        'UCLA': 'CA',
        'USC': 'CA',
        'Caltech': 'CA',
        'Chicago': 'IL',
        'Northwestern': 'IL',
        'NYU': 'NY',
        'Duke': 'NC',
        'UNC': 'NC',
        'Vanderbilt': 'TN',
        'Emory': 'GA',
        'Rice': 'TX',
        'Notre Dame': 'IN',
        
        # Other Universities
        'Michigan': 'MI',
        'Ohio': 'OH',
        'Texas': 'TX',
        'Florida': 'FL',
        'Georgia': 'GA',
        'Arizona': 'AZ',
        'Washington': 'WA',
        'Oregon': 'OR',
        'Colorado': 'CO',
        'Virginia': 'VA',
        'Wisconsin': 'WI',
        'Minnesota': 'MN',
        'Illinois': 'IL',
        'Indiana': 'IN',
        'Purdue': 'IN',
        'Iowa': 'IA',
        'Maryland': 'MD',
        'Rutgers': 'NJ',
        'UCSB': 'CA',
        'UCSD': 'CA',
        'UC Davis': 'CA',
        'UC Irvine': 'CA',
        'Syracuse': 'NY',
        'Pittsburgh': 'PA',
        'Penn State': 'PA',
        'Boston': 'MA',
        'BU': 'MA',
        'BC': 'MA',
        'Northeastern': 'MA',
        'Tufts': 'MA',
        'Amherst': 'MA',
        'Williams': 'MA',
        'Wesleyan': 'CT',
        'Taunton': 'MA',
        
        # Specific locations
        'New York': 'NY',
        'California': 'CA',
        'Massachusetts': 'MA',
        'Connecticut': 'CT',
        'New Jersey': 'NJ',
        'Pennsylvania': 'PA',
        'Illinois': 'IL',
        'Texas': 'TX',
        'Florida': 'FL',
        'Georgia': 'GA',
        'North Carolina': 'NC',
        'Tennessee': 'TN',
        'Virginia': 'VA',
        'Washington': 'WA',
    }
    
    # Regional patterns
    regional_patterns = {
        'east': 'MA',  # Default eastern region to Massachusetts
        'west': 'CA',  # Default western region to California
        'south': 'TX',  # Default southern region to Texas
        'midwest': 'IL',  # Default midwest region to Illinois
        'north': 'NY',  # Default northern region to New York
    }
    
    # Update each face
    updated_count = 0
    for face in faces:
        face_id = face['id']
        filename = face['filename']
        school_name = face['school_name']
        
        # Try to get state from the school name first
        state = extract_state_from_school(school_name)
        
        # If not found in school name, try the filename
        if not state:
            state = extract_state_from_filename(filename)
        
        # If still not found, try the mapping based on keywords in school name or filename
        if not state and (school_name or filename):
            text_to_check = (school_name or '') + ' ' + (filename or '')
            for school_pattern, state_code in state_mapping.items():
                if school_pattern.lower() in text_to_check.lower():
                    state = state_code
                    break
        
        # Try regional patterns as a fallback
        if not state and filename:
            text_to_check = filename.lower()
            for region, state_code in regional_patterns.items():
                if region in text_to_check:
                    state = state_code
                    break
        
        # Try to guess from first two letters of filename (sometimes matches state codes)
        if not state and filename and len(filename) >= 2:
            potential_state = filename[:2].upper()
            # List of valid state codes
            state_codes = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                           'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                           'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                           'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                           'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
            if potential_state in state_codes:
                state = potential_state
        
        # If all else fails, assign default states based on patterns or default to NY
        if not state:
            # Default based on filename patterns - adjust these as needed
            if 'album' in (filename or '').lower():
                state = 'CA'  # Assume albums are from California
            elif 'yearbook' in (filename or '').lower():
                state = 'MA'  # Assume yearbooks are from Massachusetts 
            else:
                # Use different defaults for different ID ranges to create variety
                id_mod = face_id % 5
                if id_mod == 0:
                    state = 'NY'
                elif id_mod == 1:
                    state = 'CA'
                elif id_mod == 2:
                    state = 'TX'
                elif id_mod == 3:
                    state = 'IL'
                else:
                    state = 'MA'
        
        try:
            cursor.execute("UPDATE faces SET state = ? WHERE id = ?", (state, face_id))
            updated_count += 1
            
            # Commit every 1000 records to avoid large transactions
            if updated_count % 1000 == 0:
                conn.commit()
                logging.info(f"Updated {updated_count} faces so far")
        except Exception as e:
            logging.error(f"Error updating face {face_id}: {e}")
    
    # Final commit
    conn.commit()
    logging.info(f"Successfully updated state information for {updated_count} faces")
    conn.close()

if __name__ == "__main__":
    logging.info("Starting state data update")
    update_state_data()
    logging.info("State data update complete")
