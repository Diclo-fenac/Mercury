"""p3_marketplace_isolation

Revision ID: 700bc93b06d3
Revises: a99999999999
Create Date: 2026-07-23 17:21:11.389848

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '700bc93b06d3'
down_revision: Union[str, Sequence[str], None] = 'a99999999999'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('catalog_items', sa.Column('seller_id', sa.String(255), nullable=True))
    op.create_index(op.f('ix_catalog_items_seller_id'), 'catalog_items', ['seller_id'], unique=False)

    op.add_column('products', sa.Column('seller_id', sa.String(255), nullable=True))
    op.create_index(op.f('ix_products_seller_id'), 'products', ['seller_id'], unique=False)

    op.add_column('tenant_users', sa.Column('seller_id', sa.String(255), nullable=True))
    op.create_index(op.f('ix_tenant_users_seller_id'), 'tenant_users', ['seller_id'], unique=False)

    op.add_column('tenant_conversations', sa.Column('seller_id', sa.String(255), nullable=True))
    op.create_index(op.f('ix_tenant_conversations_seller_id'), 'tenant_conversations', ['seller_id'], unique=False)

    op.add_column('tenant_activities', sa.Column('seller_id', sa.String(255), nullable=True))
    op.create_index(op.f('ix_tenant_activities_seller_id'), 'tenant_activities', ['seller_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_tenant_activities_seller_id'), table_name='tenant_activities')
    op.drop_column('tenant_activities', 'seller_id')

    op.drop_index(op.f('ix_tenant_conversations_seller_id'), table_name='tenant_conversations')
    op.drop_column('tenant_conversations', 'seller_id')

    op.drop_index(op.f('ix_tenant_users_seller_id'), table_name='tenant_users')
    op.drop_column('tenant_users', 'seller_id')

    op.drop_index(op.f('ix_products_seller_id'), table_name='products')
    op.drop_column('products', 'seller_id')

    op.drop_index(op.f('ix_catalog_items_seller_id'), table_name='catalog_items')
    op.drop_column('catalog_items', 'seller_id')
