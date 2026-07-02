"""multi_tenancy_setup

Revision ID: 6f6f120c13f8
Revises: d4e5f6a1b2c3
Create Date: 2026-06-21 14:19:47.651094

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '6f6f120c13f8'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a1b2c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Organizations
    op.create_table(
        'organizations',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('owner_email', sa.String(length=255), nullable=False),
        sa.Column('plan', sa.String(length=50), server_default='free', nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=True),
        sa.Column('monthly_query_limit', sa.Integer(), server_default='10000', nullable=True),
        sa.Column('monthly_index_limit', sa.Integer(), server_default='1000', nullable=True),
        sa.Column('max_products', sa.Integer(), server_default='5000', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug')
    )

    # API Keys
    op.create_table(
        'api_keys',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('key_prefix', sa.String(length=12), nullable=False),
        sa.Column('key_hash', sa.String(length=64), nullable=False),
        sa.Column('key_type', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('scopes', sa.ARRAY(sa.String()), server_default='{}', nullable=True),
        sa.Column('rate_limit_per_minute', sa.Integer(), server_default='60', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash')
    )
    op.create_index('idx_api_keys_hash', 'api_keys', ['key_hash'])
    op.create_index('idx_api_keys_org', 'api_keys', ['organization_id'])

    # Tenant Search Config
    op.create_table(
        'tenant_configs',
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('enable_semantic', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('enable_personalization', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('enable_image_search', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('rrf_keyword_weight', sa.Float(), server_default='0.6', nullable=True),
        sa.Column('rrf_vector_weight', sa.Float(), server_default='0.4', nullable=True),
        sa.Column('typo_tolerance', sa.Integer(), server_default='2', nullable=True),
        sa.Column('searchable_fields', sa.ARRAY(sa.String()), server_default='{title,description,brand,category}', nullable=True),
        sa.Column('facet_fields', sa.ARRAY(sa.String()), server_default='{brand,category}', nullable=True),
        sa.Column('widget_primary_color', sa.String(length=7), server_default='#6366f1', nullable=True),
        sa.Column('widget_font_family', sa.String(length=100), server_default='Inter', nullable=True),
        sa.Column('widget_position', sa.String(length=20), server_default='center', nullable=True),
        sa.Column('widget_placeholder', sa.Text(), server_default='Search products...', nullable=True),
        sa.Column('out_of_stock_behavior', sa.String(length=20), server_default='demote', nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('organization_id')
    )

    # Pinned Products
    op.create_table(
        'pinned_products',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('query_pattern', sa.String(length=255), nullable=False),
        sa.Column('product_id', sa.String(length=100), nullable=False),
        sa.Column('position', sa.Integer(), server_default='1', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pinned_org_query', 'pinned_products', ['organization_id', 'query_pattern'])

    # Synonyms
    op.create_table(
        'synonyms',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('term', sa.String(length=255), nullable=False),
        sa.Column('synonyms', sa.ARRAY(sa.String()), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_synonyms_org', 'synonyms', ['organization_id'])

    # Usage Events
    op.create_table(
        'usage_events',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('event_type', sa.String(length=30), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('result_count', sa.Integer(), nullable=True),
        sa.Column('api_key_id', sa.UUID(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_usage_org_time', 'usage_events', ['organization_id', 'created_at'])

    # Analytics Daily
    op.create_table(
        'analytics_daily',
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('total_queries', sa.Integer(), server_default='0', nullable=True),
        sa.Column('unique_queries', sa.Integer(), server_default='0', nullable=True),
        sa.Column('avg_latency_ms', sa.Float(), server_default='0', nullable=True),
        sa.Column('zero_result_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('cache_hit_rate', sa.Float(), server_default='0', nullable=True),
        sa.Column('top_queries', sa.JSON(), server_default='[]', nullable=True),
        sa.Column('top_zero_result_queries', sa.JSON(), server_default='[]', nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('organization_id', 'date')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('analytics_daily')
    op.drop_index('idx_usage_org_time', 'usage_events')
    op.drop_table('usage_events')
    op.drop_index('idx_synonyms_org', 'synonyms')
    op.drop_table('synonyms')
    op.drop_index('idx_pinned_org_query', 'pinned_products')
    op.drop_table('pinned_products')
    op.drop_table('tenant_configs')
    op.drop_index('idx_api_keys_org', 'api_keys')
    op.drop_index('idx_api_keys_hash', 'api_keys')
    op.drop_table('api_keys')
    op.drop_table('organizations')
