"""p2_catalog_integrations

Revision ID: a99999999999
Revises: 9850421371a2
Create Date: 2026-07-23 11:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a99999999999'
down_revision: Union[str, None] = '9850421371a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('catalog_integrations',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('integration_type', sa.String(length=50), nullable=False),
    sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
    sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('sync_status', sa.String(length=50), nullable=True),
    sa.Column('last_error', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_catalog_integrations_org', 'catalog_integrations', ['organization_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_catalog_integrations_org', table_name='catalog_integrations')
    op.drop_table('catalog_integrations')
