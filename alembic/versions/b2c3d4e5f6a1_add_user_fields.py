"""Add gender, health, location, behavior index to users

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-04-27 11:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'b2c3d4e5f6a1'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('gender', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('health', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('users', sa.Column('location', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.create_index('idx_users_behavior', 'users', ['behavior'], unique=False, postgresql_using='gin')


def downgrade() -> None:
    op.drop_index('idx_users_behavior', table_name='users', postgresql_using='gin')
    op.drop_column('users', 'location')
    op.drop_column('users', 'health')
    op.drop_column('users', 'gender')
