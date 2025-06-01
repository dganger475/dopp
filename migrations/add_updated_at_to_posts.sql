-- Add updated_at column to posts table if it doesn't exist
ALTER TABLE posts ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Update existing rows to set updated_at equal to created_at
UPDATE posts SET updated_at = created_at WHERE updated_at IS NULL; 