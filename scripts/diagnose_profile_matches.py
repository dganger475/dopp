#!/usr/bin/env python3
"""
Diagnostic script to identify why user matches aren't showing in profile.
This will directly query the database to show all user matches.
"""

import logging
import os
import sqlite3
import sys

from flask import Flask, session

# Set up basic logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define database paths using hardcoded path from app.py
ROOT_DIR = r"C:\Users\1439\Documents\DopplegangerApp"
USERS_DB_PATH = os.path.join(ROOT_DIR, 'users.db')

def get_db_connection(db_path):
    """Connect to the specified SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def get_all_user_matches():
    """Get a count of all matches in the database."""
    conn = get_db_connection(USERS_DB_PATH)
    if not conn:
        return "Failed to connect to database"
    
    try:
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM user_matches")
        total_count = cursor.fetchone()[0]
        
        # Count by visibility
        cursor.execute("SELECT COUNT(*) FROM user_matches WHERE is_visible = 1")
        visible_count = cursor.fetchone()[0]
        
        # Count by privacy level
        cursor.execute("SELECT privacy_level, COUNT(*) FROM user_matches GROUP BY privacy_level")
        privacy_counts = cursor.fetchall()
        
        # Get matches by user
        cursor.execute("""
            SELECT user_id, COUNT(*) as match_count 
            FROM user_matches 
            GROUP BY user_id
        """)
        user_counts = cursor.fetchall()
        
        # Get a sample of actual matches
        cursor.execute("""
            SELECT * FROM user_matches
            LIMIT 10
        """)
        sample_matches = cursor.fetchall()
        
        results = {
            "total_matches": total_count,
            "visible_matches": visible_count,
            "privacy_counts": {level: count for level, count in privacy_counts},
            "user_counts": {user_id: count for user_id, count in user_counts},
            "sample_matches": [dict(match) for match in sample_matches]
        }
        
        return results
    except Exception as e:
        logger.error(f"Error fetching user matches: {e}")
        return f"Error: {str(e)}"
    finally:
        conn.close()

def get_matches_for_user(user_id):
    """Get all matches for a specific user ID."""
    conn = get_db_connection(USERS_DB_PATH)
    if not conn:
        return "Failed to connect to database"
    
    try:
        cursor = conn.cursor()
        
        # Get all matches for the user
        cursor.execute("""
            SELECT * FROM user_matches
            WHERE user_id = ?
        """, (user_id,))
        
        user_matches = cursor.fetchall()
        
        if not user_matches:
            return f"No matches found for user ID {user_id}"
        
        match_data = []
        for match in user_matches:
            match_dict = dict(match)
            # Get match details if available
            try:
                cursor.execute("""
                    SELECT * FROM match_metadata
                    WHERE match_filename = ?
                """, (match_dict.get('match_filename'),))
                metadata = cursor.fetchone()
                if metadata:
                    match_dict['metadata'] = dict(metadata)
            except Exception as e:
                match_dict['metadata_error'] = str(e)
            
            match_data.append(match_dict)
        
        return {
            "user_id": user_id,
            "match_count": len(match_data),
            "matches": match_data
        }
    except Exception as e:
        logger.error(f"Error fetching user matches: {e}")
        return f"Error: {str(e)}"
    finally:
        conn.close()

if __name__ == "__main__":
    print("\n=== DATABASE MATCHES DIAGNOSTIC ===")
    
    all_matches = get_all_user_matches()
    print("\n--- OVERALL MATCH STATISTICS ---")
    if isinstance(all_matches, dict):
        print(f"Total matches in database: {all_matches['total_matches']}")
        print(f"Visible matches: {all_matches['visible_matches']}")
        print(f"Privacy level counts: {all_matches['privacy_counts']}")
        print(f"Matches by user: {all_matches['user_counts']}")
        
        if all_matches['user_counts']:
            user_id = next(iter(all_matches['user_counts'].keys()))
            print(f"\n--- SAMPLE USER ({user_id}) MATCHES ---")
            user_matches = get_matches_for_user(user_id)
            if isinstance(user_matches, dict):
                print(f"User has {user_matches['match_count']} matches")
                for i, match in enumerate(user_matches['matches']):
                    print(f"\nMatch {i+1}:")
                    print(f"  ID: {match.get('id')}")
                    print(f"  Match filename: {match.get('match_filename')}")
                    print(f"  Visible: {'Yes' if match.get('is_visible') == 1 else 'No'}")
                    print(f"  Privacy: {match.get('privacy_level')}")
                    print(f"  Similarity: {match.get('similarity')}")
            else:
                print(user_matches)
    else:
        print(all_matches)
    
    print("\n=== END OF DIAGNOSTIC ===")
