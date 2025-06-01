"""add updated_at column

Revision ID: add_updated_at_column
Revises: 
Create Date: 2025-05-30 14:56:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_updated_at_column'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add updated_at column with default value of current timestamp
    op.add_column('users', sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    
    # Update existing rows to have the same value as created_at
    op.execute("UPDATE users SET updated_at = created_at WHERE updated_at IS NULL")

def downgrade():
    # Remove the updated_at column
    op.drop_column('users', 'updated_at') 