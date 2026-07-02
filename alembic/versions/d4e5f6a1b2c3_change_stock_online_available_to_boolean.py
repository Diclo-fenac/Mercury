"""Change stock and online_available to Boolean

Revision ID: d4e5f6a1b2c3
Revises: c3d4e5f6a1b2
Create Date: 2026-04-27 14:35:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'd4e5f6a1b2c3'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE products ALTER COLUMN stock TYPE BOOLEAN USING stock::boolean")
    op.execute("ALTER TABLE products ALTER COLUMN online_available TYPE BOOLEAN USING online_available::boolean")


def downgrade() -> None:
    op.execute("ALTER TABLE products ALTER COLUMN online_available TYPE INTEGER USING CASE WHEN online_available THEN 1 ELSE 0 END")
    op.execute("ALTER TABLE products ALTER COLUMN stock TYPE INTEGER USING CASE WHEN stock THEN 1 ELSE 0 END")
