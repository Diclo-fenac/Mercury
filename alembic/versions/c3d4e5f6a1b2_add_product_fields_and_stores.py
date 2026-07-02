"""Add product fields and stores table

Revision ID: c3d4e5f6a1b2
Revises: b2c3d4e5f6a1
Create Date: 2026-04-27 11:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'c3d4e5f6a1b2'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # New product columns
    op.add_column('products', sa.Column('title', sa.String(length=500), nullable=True))
    op.add_column('products', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('products', sa.Column('url', sa.Text(), nullable=True))
    op.add_column('products', sa.Column('images', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('products', sa.Column('availability', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('products', sa.Column('price_history', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('products', sa.Column('uploaded_at', sa.DateTime(), nullable=True))
    op.create_index('idx_products_availability', 'products', ['availability'], unique=False, postgresql_using='gin')

    # Stores table
    op.create_table(
        'stores',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=True),
        sa.Column('location', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('hours', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('aisle_mapping', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('connected_stores', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_stores_location', 'stores', ['location'], unique=False, postgresql_using='gin')


def downgrade() -> None:
    op.drop_index('idx_stores_location', table_name='stores', postgresql_using='gin')
    op.drop_table('stores')
    op.drop_index('idx_products_availability', table_name='products', postgresql_using='gin')
    op.drop_column('products', 'uploaded_at')
    op.drop_column('products', 'price_history')
    op.drop_column('products', 'availability')
    op.drop_column('products', 'images')
    op.drop_column('products', 'url')
    op.drop_column('products', 'description')
    op.drop_column('products', 'title')
