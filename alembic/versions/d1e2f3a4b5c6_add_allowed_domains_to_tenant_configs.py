"""add allowed_domains to tenant_configs

Revision ID: d1e2f3a4b5c6
Revises: ea912c6ecc4d
Create Date: 2026-07-25 15:51:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = 'ea912c6ecc4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE tenant_configs "
        "ADD COLUMN IF NOT EXISTS allowed_domains VARCHAR[] DEFAULT '{}'"
    )


def downgrade() -> None:
    op.drop_column('tenant_configs', 'allowed_domains')
