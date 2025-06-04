"""Create faces table migration
============================

This migration creates the faces table for storing face encodings.
"""

from flask import current_app
from flask_migrate import upgrade
from extensions import db

def upgrade():
    """Create faces table."""
    try:
        # Create faces table
        db.session.execute("""
            CREATE TABLE IF NOT EXISTS faces (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                face_encoding BYTEA NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on user_id for faster lookups
        db.session.execute("""
            CREATE INDEX IF NOT EXISTS idx_faces_user_id ON faces(user_id)
        """)
        
        # Create trigger to update updated_at timestamp
        db.session.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)
        
        db.session.execute("""
            CREATE TRIGGER update_faces_updated_at
                BEFORE UPDATE ON faces
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """)
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise

def downgrade():
    """Drop faces table."""
    try:
        # Drop trigger first
        db.session.execute("""
            DROP TRIGGER IF EXISTS update_faces_updated_at ON faces;
        """)
        
        # Drop function
        db.session.execute("""
            DROP FUNCTION IF EXISTS update_updated_at_column();
        """)
        
        # Drop table
        db.session.execute("""
            DROP TABLE IF EXISTS faces;
        """)
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise 