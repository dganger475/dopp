from flask import current_app
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def get_db_connection():
    db_url = current_app.config['SQLALCHEMY_DATABASE_URI']
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()

def upgrade():
    conn = get_db_connection()
    cursor = conn.connection.cursor()
    
    # Create faces table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faces (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            face_encoding BYTEA NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Add index on user_id for faster lookups
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_faces_user_id ON faces(user_id)
    """)
    
    conn.connection.commit()
    conn.close()

def downgrade():
    conn = get_db_connection()
    cursor = conn.connection.cursor()
    
    # Drop the faces table
    cursor.execute("DROP TABLE IF EXISTS faces")
    
    conn.connection.commit()
    conn.close() 