"""Add barcodes table

Revision ID: a1b2c3d4e5f6
Revises: f6fa0b53e9bc
Create Date: 2026-04-27 10:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f6fa0b53e9bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'barcodes',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('barcode', sa.String(length=255), nullable=False),
        sa.Column('barcode_type', sa.String(length=50), nullable=True),
        sa.Column('pid', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_barcodes_pid', 'barcodes', ['pid'], unique=False)
    op.create_index('idx_barcodes_barcode', 'barcodes', ['barcode'], unique=False)
    op.create_index('idx_barcodes_status', 'barcodes', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_barcodes_status', table_name='barcodes')
    op.drop_index('idx_barcodes_barcode', table_name='barcodes')
    op.drop_index('idx_barcodes_pid', table_name='barcodes')
    op.drop_table('barcodes')
