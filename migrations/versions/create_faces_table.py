"""create faces table

Revision ID: create_faces_table
Revises: add_profile_photo_column
Create Date: 2024-03-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_faces_table'
down_revision = 'add_profile_photo_column'
branch_labels = None
depends_on = None

def upgrade():
    # Create faces table
    op.create_table('faces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('image_path', sa.String(length=255), nullable=False),
        sa.Column('encoding', postgresql.BYTEA(), nullable=True),
        sa.Column('yearbook_year', sa.String(length=50), nullable=True),
        sa.Column('school_name', sa.String(length=255), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('decade', sa.String(length=50), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('claimed_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['claimed_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('filename')
    )
    
    # Create index on claimed_by_user_id for faster lookups
    op.create_index(op.f('ix_faces_claimed_by_user_id'), 'faces', ['claimed_by_user_id'], unique=False)

def downgrade():
    # Drop index
    op.drop_index(op.f('ix_faces_claimed_by_user_id'), table_name='faces')
    
    # Drop faces table
    op.drop_table('faces') 