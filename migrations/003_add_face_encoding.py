def upgrade():
    # Add face_encoding column to users table
    conn = get_users_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        ALTER TABLE users 
        ADD COLUMN face_encoding BLOB
    """)
    conn.commit()
    conn.close()

def downgrade():
    # Remove face_encoding column from users table
    conn = get_users_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        ALTER TABLE users 
        DROP COLUMN face_encoding
    """)
    conn.commit()
    conn.close()
