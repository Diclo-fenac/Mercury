"""p3_commerce_opt

Revision ID: ea8f1a0721a5
Revises: 1e97e0828f95
Create Date: 2026-07-23 17:25:14.763616

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ea8f1a0721a5'
down_revision: Union[str, Sequence[str], None] = '1e97e0828f95'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('products', sa.Column('margin', sa.Float(), nullable=True))
    op.add_column('products', sa.Column('target_revenue', sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('products', 'target_revenue')
    op.drop_column('products', 'margin')
