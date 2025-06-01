"""add profile photo column

Revision ID: add_profile_photo
Revises: 
Create Date: 2025-05-30 14:48:43.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_profile_photo'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add profile_photo column to users table
    op.add_column('users', sa.Column('profile_photo', sa.String(255), nullable=True))

def downgrade():
    # Remove profile_photo column from users table
    op.drop_column('users', 'profile_photo') 