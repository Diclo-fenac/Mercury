"""p2_opt_in_personalization

Revision ID: 9850421371a2
Revises: 24a0682e0804
Create Date: 2026-07-23 16:43:52.878448

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9850421371a2'
down_revision: Union[str, Sequence[str], None] = '24a0682e0804'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tenant_users', sa.Column('has_consented_to_personalization', sa.Boolean(), server_default='false', nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tenant_users', 'has_consented_to_personalization')
