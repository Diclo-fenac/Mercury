"""catalog index outbox

Revision ID: 8b02c3d5e9f1
Revises: 7a91b2c4d8e0
Create Date: 2026-07-23 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '8b02c3d5e9f1'
down_revision: Union[str, Sequence[str], None] = '7a91b2c4d8e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Track catalog-item indexing and persist replayable index events."""
    op.add_column('catalog_items', sa.Column('index_version', sa.Integer(), server_default='1', nullable=False))
    op.add_column('catalog_items', sa.Column('index_status', sa.String(length=20), server_default='pending', nullable=False))
    op.add_column('catalog_items', sa.Column('index_error', sa.Text(), nullable=True))
    op.add_column('catalog_items', sa.Column('indexed_at', sa.DateTime(timezone=True), nullable=True))
    op.create_check_constraint(
        'ck_catalog_items_index_status',
        'catalog_items',
        "index_status IN ('pending', 'processing', 'indexed', 'failed', 'dead')",
    )
    op.create_index(
        'idx_catalog_items_index_status',
        'catalog_items',
        ['organization_id', 'catalog_id', 'index_status'],
    )

    op.create_table(
        'catalog_index_events',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('catalog_id', sa.UUID(), nullable=False),
        sa.Column('catalog_item_id', sa.UUID(), nullable=False),
        sa.Column('item_version', sa.Integer(), nullable=False),
        sa.Column('operation', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('attempts', sa.Integer(), server_default='0', nullable=False),
        sa.Column('payload', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('available_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint("operation IN ('upsert', 'delete')", name='ck_catalog_index_events_operation'),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'indexed', 'failed', 'dead')",
            name='ck_catalog_index_events_status',
        ),
        sa.ForeignKeyConstraint(
            ['catalog_item_id', 'catalog_id', 'organization_id'],
            ['catalog_items.id', 'catalog_items.catalog_id', 'catalog_items.organization_id'],
            ondelete='CASCADE',
            name='fk_catalog_index_events_catalog_item',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'idx_catalog_index_events_pending',
        'catalog_index_events',
        ['organization_id', 'catalog_id', 'status', 'available_at'],
    )
    op.create_index(
        'idx_catalog_index_events_item_version',
        'catalog_index_events',
        ['catalog_item_id', 'item_version'],
    )


def downgrade() -> None:
    """Remove durable index state after all dependent workers are stopped."""
    op.drop_index('idx_catalog_index_events_item_version', table_name='catalog_index_events')
    op.drop_index('idx_catalog_index_events_pending', table_name='catalog_index_events')
    op.drop_table('catalog_index_events')
    op.drop_index('idx_catalog_items_index_status', table_name='catalog_items')
    op.drop_constraint('ck_catalog_items_index_status', 'catalog_items', type_='check')
    op.drop_column('catalog_items', 'indexed_at')
    op.drop_column('catalog_items', 'index_error')
    op.drop_column('catalog_items', 'index_status')
    op.drop_column('catalog_items', 'index_version')
