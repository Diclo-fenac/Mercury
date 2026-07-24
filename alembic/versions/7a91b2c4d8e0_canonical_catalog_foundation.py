"""canonical catalog foundation

Revision ID: 7a91b2c4d8e0
Revises: 6f6f120c13f8
Create Date: 2026-07-23 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '7a91b2c4d8e0'
down_revision: Union[str, Sequence[str], None] = '6f6f120c13f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add tenant-owned catalog primitives without modifying the legacy products table."""
    op.add_column(
        'organizations',
        sa.Column('region', sa.String(length=32), server_default=sa.text("'us-east-1'"), nullable=False),
    )
    op.create_check_constraint('ck_organizations_region', 'organizations', "region <> ''")
    op.execute(
        "ALTER TABLE tenant_configs "
        "ADD COLUMN IF NOT EXISTS webhook_urls VARCHAR[] DEFAULT '{}'"
    )

    op.create_table(
        'merchant_stores',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column('settings', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE', name='fk_merchant_stores_organization'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id', 'organization_id', name='uq_merchant_stores_id_organization'),
        sa.UniqueConstraint('organization_id', 'slug', name='uq_merchant_stores_org_slug'),
        sa.UniqueConstraint('organization_id', 'external_id', name='uq_merchant_stores_org_external_id'),
    )
    op.create_index('idx_merchant_stores_org_status', 'merchant_stores', ['organization_id', 'status'])

    op.create_table(
        'sellers',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column('metadata', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE', name='fk_sellers_organization'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id', 'organization_id', name='uq_sellers_id_organization'),
        sa.UniqueConstraint('organization_id', 'slug', name='uq_sellers_org_slug'),
        sa.UniqueConstraint('organization_id', 'external_id', name='uq_sellers_org_external_id'),
    )
    op.create_index('idx_sellers_org_status', 'sellers', ['organization_id', 'status'])

    op.create_table(
        'catalogs',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('store_id', sa.UUID(), nullable=True),
        sa.Column('seller_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=20), server_default='product', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column('settings', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint("resource_type IN ('product', 'document', 'asset', 'content')", name='ck_catalogs_resource_type'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE', name='fk_catalogs_organization'),
        sa.ForeignKeyConstraint(['store_id', 'organization_id'], ['merchant_stores.id', 'merchant_stores.organization_id'], name='fk_catalogs_store_organization'),
        sa.ForeignKeyConstraint(['seller_id', 'organization_id'], ['sellers.id', 'sellers.organization_id'], name='fk_catalogs_seller_organization'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id', 'organization_id', name='uq_catalogs_id_organization'),
        sa.UniqueConstraint('organization_id', 'slug', name='uq_catalogs_org_slug'),
    )
    op.create_index('idx_catalogs_org_status', 'catalogs', ['organization_id', 'status'])

    op.create_table(
        'catalog_items',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('catalog_id', sa.UUID(), nullable=False),
        sa.Column('parent_item_id', sa.UUID(), nullable=True),
        sa.Column('external_id', sa.String(length=512), nullable=False),
        sa.Column('resource_type', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.Text(), nullable=True),
        sa.Column('brand', sa.String(length=255), nullable=True),
        sa.Column('category', sa.String(length=255), nullable=True),
        sa.Column('sub_category', sa.String(length=255), nullable=True),
        sa.Column('document', postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('source_system', sa.String(length=50), server_default='manual', nullable=False),
        sa.Column('source_version', sa.String(length=255), nullable=True),
        sa.Column('source_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.CheckConstraint("resource_type IN ('product', 'document', 'asset', 'content')", name='ck_catalog_items_resource_type'),
        sa.ForeignKeyConstraint(['catalog_id', 'organization_id'], ['catalogs.id', 'catalogs.organization_id'], ondelete='CASCADE', name='fk_catalog_items_catalog_organization'),
        sa.ForeignKeyConstraint(['parent_item_id', 'catalog_id', 'organization_id'], ['catalog_items.id', 'catalog_items.catalog_id', 'catalog_items.organization_id'], name='fk_catalog_items_parent_catalog_organization'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id', 'catalog_id', 'organization_id', name='uq_catalog_items_id_catalog_org'),
        sa.UniqueConstraint('organization_id', 'catalog_id', 'external_id', name='uq_catalog_items_org_catalog_external_id'),
    )
    op.create_index('idx_catalog_items_org_catalog_type_status', 'catalog_items', ['organization_id', 'catalog_id', 'resource_type', 'status'])
    op.create_index('idx_catalog_items_parent', 'catalog_items', ['parent_item_id'])
    op.create_index('idx_catalog_items_document', 'catalog_items', ['document'], postgresql_using='gin')


def downgrade() -> None:
    """Remove canonical catalog structures in reverse dependency order."""
    op.drop_index('idx_catalog_items_document', table_name='catalog_items')
    op.drop_index('idx_catalog_items_parent', table_name='catalog_items')
    op.drop_index('idx_catalog_items_org_catalog_type_status', table_name='catalog_items')
    op.drop_table('catalog_items')
    op.drop_index('idx_catalogs_org_status', table_name='catalogs')
    op.drop_table('catalogs')
    op.drop_index('idx_sellers_org_status', table_name='sellers')
    op.drop_table('sellers')
    op.drop_index('idx_merchant_stores_org_status', table_name='merchant_stores')
    op.drop_table('merchant_stores')
    op.drop_column('tenant_configs', 'webhook_urls')
    op.drop_constraint('ck_organizations_region', 'organizations', type_='check')
    op.drop_column('organizations', 'region')
