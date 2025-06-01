import os
import sqlite3
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import time
from tqdm import tqdm
from datetime import datetime
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import islice
import multiprocessing

# Load environment variables
load_dotenv()

BATCH_SIZE = 5000  # Increased batch size
MAX_WORKERS = multiprocessing.cpu_count()  # Use number of CPU cores
MIGRATION_STATE_FILE = 'migration_state.json'

def get_sqlite_connection():
    """Connect to SQLite database."""
    return sqlite3.connect('faces.db')

def get_postgres_connection():
    """Connect to PostgreSQL database with proper error handling."""
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {str(e)}")
        raise

def get_table_count(cursor, table_name):
    """Get the number of rows in a table."""
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    return cursor.fetchone()[0]

def load_migration_state():
    """Load the migration state from file."""
    if os.path.exists(MIGRATION_STATE_FILE):
        with open(MIGRATION_STATE_FILE, 'r') as f:
            return json.load(f)
    return {'completed_tables': []}

def save_migration_state(state):
    """Save the migration state to file."""
    with open(MIGRATION_STATE_FILE, 'w') as f:
        json.dump(state, f)

def get_table_schema(sqlite_cursor, table_name):
    """Get the table schema from SQLite and convert to PostgreSQL format."""
    sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
    columns = sqlite_cursor.fetchall()
    
    # Map SQLite types to PostgreSQL types
    type_mapping = {
        'INTEGER': 'INTEGER',
        'REAL': 'DOUBLE PRECISION',
        'TEXT': 'TEXT',
        'BLOB': 'BYTEA',
        'BOOLEAN': 'BOOLEAN',
        'DATETIME': 'TIMESTAMP',
        'DATE': 'DATE',
        'TIMESTAMP': 'TIMESTAMP'
    }
    
    # List of boolean columns
    boolean_columns = [
        'is_claimed', 'is_admin', 'is_verified', 'is_active', 
        'share_real_name', 'share_location', 'is_private',
        'is_deleted', 'is_blocked', 'is_muted', 'share_age'
    ]
    
    # Build CREATE TABLE statement
    column_defs = []
    for col in columns:
        name = col[1]
        type_ = col[2].upper()
        nullable = "NOT NULL" if col[3] else ""
        default = col[4]
        
        # Map the type
        pg_type = type_mapping.get(type_, 'TEXT')
        
        # Special handling for boolean fields
        if name in boolean_columns:
            pg_type = 'BOOLEAN'
            # Convert default value for boolean fields
            if default is not None:
                if default == '0':
                    default = 'FALSE'
                elif default == '1':
                    default = 'TRUE'
                else:
                    default = None
        
        # Special handling for date and timestamp fields
        if name in ['birthdate', 'created_at', 'updated_at', 'last_login']:
            if name == 'birthdate':
                pg_type = 'DATE'
            else:
                pg_type = 'TIMESTAMP'
        
        # Handle AUTOINCREMENT
        if 'AUTOINCREMENT' in type_:
            pg_type = 'SERIAL'
            type_ = type_.replace('AUTOINCREMENT', '').strip()
        
        # Add default value if present
        if default is not None:
            # Handle boolean defaults
            if pg_type == 'BOOLEAN':
                if default == '0':
                    default = 'FALSE'
                elif default == '1':
                    default = 'TRUE'
                else:
                    default = None
            
            if default is not None:
                default = f"DEFAULT {default}"
            else:
                default = ""
        else:
            default = ""
        
        column_defs.append(f"{name} {pg_type} {nullable} {default}".strip())
    
    return f"CREATE TABLE IF NOT EXISTS {table_name} (\n    " + ",\n    ".join(column_defs) + "\n);"

def get_postgres_type(sqlite_type, default_value=None):
    """Convert SQLite type to PostgreSQL type with proper handling of booleans."""
    sqlite_type = sqlite_type.lower()
    
    # Handle boolean types
    if sqlite_type in ('boolean', 'bool'):
        return 'boolean'
    
    # Handle integer types
    if sqlite_type in ('integer', 'int'):
        # If default value is 0 or 1, treat as boolean
        if default_value in ('0', '1'):
            return 'boolean'
        return 'integer'
    
    # Handle other types
    type_mapping = {
        'text': 'text',
        'varchar': 'varchar',
        'real': 'double precision',
        'float': 'double precision',
        'double': 'double precision',
        'decimal': 'numeric',
        'numeric': 'numeric',
        'date': 'date',
        'datetime': 'timestamp',
        'timestamp': 'timestamp',
        'blob': 'bytea'
    }
    
    return type_mapping.get(sqlite_type, 'text')

def check_table_exists(pg_cursor, table_name):
    """Check if a table exists in PostgreSQL."""
    try:
        pg_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, (table_name,))
        return pg_cursor.fetchone()[0]
    except Exception:
        return False

def create_table(pg_conn, pg_cursor, sqlite_cursor, table_name):
    """Create a table in PostgreSQL with proper type handling."""
    try:
        # Check if table already exists
        table_exists = check_table_exists(pg_cursor, table_name)

        if table_exists:
            print(f"Table {table_name} already exists, skipping creation")
            return True

        # Convert SQLite schema to PostgreSQL schema
        pg_schema = get_table_schema(sqlite_cursor, table_name)
        
        # Execute the CREATE TABLE statement
        pg_cursor.execute(pg_schema)
        pg_conn.commit()  # Explicitly commit the table creation
        
        # Verify table was created
        if not check_table_exists(pg_cursor, table_name):
            print(f"Failed to create table {table_name}")
            return False
            
        print(f"Created table {table_name}")
        return True
        
    except Exception as e:
        print(f"Error creating table {table_name}: {str(e)}")
        pg_conn.rollback()
        return False

def process_batch(batch_data):
    """Process a batch of rows in parallel."""
    table_name, batch, columns, insert_sql = batch_data
    pg_conn = get_postgres_connection()
    pg_cursor = pg_conn.cursor()
    
    try:
        processed_rows = [process_row(row, columns) for row in batch]
        pg_cursor.executemany(insert_sql, processed_rows)
        pg_conn.commit()
        return len(processed_rows)
    except Exception as e:
        pg_conn.rollback()
        print(f"\nError processing batch: {str(e)}")
        return 0
    finally:
        pg_cursor.close()
        pg_conn.close()

def process_row(row, columns):
    """Process a row to handle data type conversions."""
    processed_row = list(row)
    
    # Find column indices
    birthdate_idx = next((i for i, col in enumerate(columns) if col[1] == 'birthdate'), None)
    created_at_idx = next((i for i, col in enumerate(columns) if col[1] == 'created_at'), None)
    updated_at_idx = next((i for i, col in enumerate(columns) if col[1] == 'updated_at'), None)
    last_login_idx = next((i for i, col in enumerate(columns) if col[1] == 'last_login'), None)
    is_claimed_idx = next((i for i, col in enumerate(columns) if col[1] == 'is_claimed'), None)
    is_admin_idx = next((i for i, col in enumerate(columns) if col[1] == 'is_admin'), None)
    is_verified_idx = next((i for i, col in enumerate(columns) if col[1] == 'is_verified'), None)
    is_active_idx = next((i for i, col in enumerate(columns) if col[1] == 'is_active'), None)
    share_location_idx = next((i for i, col in enumerate(columns) if col[1] == 'share_location'), None)
    is_private_idx = next((i for i, col in enumerate(columns) if col[1] == 'is_private'), None)
    is_deleted_idx = next((i for i, col in enumerate(columns) if col[1] == 'is_deleted'), None)
    is_blocked_idx = next((i for i, col in enumerate(columns) if col[1] == 'is_blocked'), None)
    is_muted_idx = next((i for i, col in enumerate(columns) if col[1] == 'is_muted'), None)
    share_real_name_idx = next((i for i, col in enumerate(columns) if col[1] == 'share_real_name'), None)
    share_age_idx = next((i for i, col in enumerate(columns) if col[1] == 'share_age'), None)
    
    # Convert timestamps
    for idx in [created_at_idx, updated_at_idx, last_login_idx]:
        if idx is not None and row[idx] is not None:
            try:
                timestamp = int(row[idx])
                if timestamp > 0:  # Only convert if timestamp is valid
                    dt = datetime.fromtimestamp(timestamp)
                    processed_row[idx] = dt
                else:
                    processed_row[idx] = None
            except (ValueError, TypeError):
                processed_row[idx] = None
    
    # Convert birthdate
    if birthdate_idx is not None and row[birthdate_idx] is not None:
        try:
            timestamp = int(row[birthdate_idx])
            if timestamp > 0:  # Only convert if timestamp is valid
                dt = datetime.fromtimestamp(timestamp)
                processed_row[birthdate_idx] = dt.date()
            else:
                processed_row[birthdate_idx] = None
        except (ValueError, TypeError):
            processed_row[birthdate_idx] = None
    
    # Convert boolean fields
    boolean_indices = [
        is_claimed_idx, is_admin_idx, is_verified_idx, is_active_idx, 
        share_location_idx, is_private_idx, is_deleted_idx, 
        is_blocked_idx, is_muted_idx, share_real_name_idx, share_age_idx
    ]
    
    for idx in boolean_indices:
        if idx is not None:
            try:
                value = row[idx]
                if value is None:
                    processed_row[idx] = None
                elif isinstance(value, (int, float)):
                    processed_row[idx] = bool(value)
                elif isinstance(value, str):
                    processed_row[idx] = value.lower() in ('true', '1', 't', 'yes')
                else:
                    processed_row[idx] = bool(value)
            except (ValueError, TypeError):
                processed_row[idx] = None
    
    return processed_row

def reset_transaction(pg_conn):
    """Reset an aborted transaction."""
    try:
        pg_conn.rollback()
    except Exception:
        pass

def check_table_has_data(pg_cursor, table_name):
    """Check if a table has data in PostgreSQL."""
    try:
        pg_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return pg_cursor.fetchone()[0] > 0
    except Exception:
        return False

def get_table_dependencies():
    """Get the order of tables based on their dependencies."""
    return [
        'alembic_version',
        'users',
        'faces',
        'face_likes',
        'reactions',
        'matches',
        'notifications',
        'claimed_profiles',
        'likes',
        'follows',
        'user_matches',
        'posts',
        'comments',
        'feed_posts',
        'user_saved_matches'
    ]

def migrate_table(sqlite_conn, table_name):
    """Migrate a table from SQLite to PostgreSQL with proper type handling."""
    sqlite_cursor = None
    pg_conn = None
    pg_cursor = None
    
    try:
        # Initialize cursors
        sqlite_cursor = sqlite_conn.cursor()
        pg_conn = get_postgres_connection()
        pg_cursor = pg_conn.cursor()
        
        # Create table if it doesn't exist
        if not create_table(pg_conn, pg_cursor, sqlite_cursor, table_name):
            print(f"Failed to create table {table_name}, skipping migration")
            return
        
        # Verify table exists
        if not check_table_exists(pg_cursor, table_name):
            print(f"Table {table_name} does not exist after creation, skipping migration")
            return
        
        # Check if table has data
        if check_table_has_data(pg_cursor, table_name):
            print(f"Table {table_name} already has data, skipping migration")
            return
        
        # Get column info for type conversion
        sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
        columns = sqlite_cursor.fetchall()
        
        # Build column list for SELECT
        column_names = [col[1] for col in columns]
        columns_str = ', '.join(column_names)
        
        # Get data from SQLite
        sqlite_cursor.execute(f"SELECT {columns_str} FROM {table_name}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"No data to migrate for table {table_name}")
            return
        
        # Process rows to handle type conversions
        processed_rows = [process_row(row, columns) for row in rows]
        
        # Prepare INSERT statement
        placeholders = ', '.join(['%s'] * len(column_names))
        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        # Insert data into PostgreSQL
        pg_cursor.executemany(insert_sql, processed_rows)
        pg_conn.commit()  # Explicitly commit the data insertion
        
        print(f"Migrated {len(rows)} rows from {table_name}")
        
    except Exception as e:
        print(f"Error migrating table {table_name}: {str(e)}")
        if pg_conn:
            pg_conn.rollback()
        raise
    finally:
        if sqlite_cursor:
            sqlite_cursor.close()
        if pg_cursor:
            pg_cursor.close()
        if pg_conn:
            pg_conn.close()

def migrate_data():
    """Main migration function with proper error handling."""
    sqlite_conn = None
    
    try:
        # Connect to SQLite database
        sqlite_conn = get_sqlite_connection()
        
        # Get tables in dependency order
        tables = [(name,) for name in get_table_dependencies()]
        
        # First pass: Create all tables
        print("Creating tables...")
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':  # Skip system tables
                try:
                    pg_conn = get_postgres_connection()
                    pg_cursor = pg_conn.cursor()
                    sqlite_cursor = sqlite_conn.cursor()
                    try:
                        if not create_table(pg_conn, pg_cursor, sqlite_cursor, table_name):
                            print(f"Failed to create table {table_name}, will retry during data migration")
                    finally:
                        sqlite_cursor.close()
                        pg_cursor.close()
                        pg_conn.close()
                except Exception as e:
                    print(f"Error creating table {table_name}: {str(e)}")
                    continue
        
        # Calculate total rows to migrate
        total_rows = 0
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':  # Skip system tables
                sqlite_cursor = sqlite_conn.cursor()
                pg_conn = get_postgres_connection()
                pg_cursor = pg_conn.cursor()
                try:
                    # Verify table exists and check data
                    if check_table_exists(pg_cursor, table_name) and not check_table_has_data(pg_cursor, table_name):
                        total_rows += get_table_count(sqlite_cursor, table_name)
                finally:
                    sqlite_cursor.close()
                    pg_cursor.close()
                    pg_conn.close()
        
        # Second pass: Migrate data
        print("\nMigrating data...")
        with tqdm(total=total_rows, desc="Starting migration...") as pbar:
            for table in tables:
                table_name = table[0]
                # Skip sqlite_sequence table
                if table_name == 'sqlite_sequence':
                    print(f"Skipping system table: {table_name}")
                    continue
                
                try:
                    migrate_table(sqlite_conn, table_name)
                    # Update progress bar with actual migrated rows
                    pg_conn = get_postgres_connection()
                    pg_cursor = pg_conn.cursor()
                    try:
                        if check_table_has_data(pg_cursor, table_name):
                            pg_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                            pg_count = pg_cursor.fetchone()[0]
                            pbar.update(pg_count)
                    except Exception:
                        pass
                    finally:
                        pg_cursor.close()
                        pg_conn.close()
                except Exception as e:
                    print(f"Error during migration: {str(e)}")
                    continue  # Continue with next table instead of raising
                
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        raise
    finally:
        if sqlite_conn:
            sqlite_conn.close()

if __name__ == "__main__":
    migrate_data() 