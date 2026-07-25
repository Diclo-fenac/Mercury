"""
SQLAlchemy Models for Multi-Tenancy
"""
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.sql import func

from app.infrastructure.db.models import Base


class Organization(Base):
    """Organizations table representing a SaaS tenant"""
    __tablename__ = 'organizations'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    owner_email = Column(String(255), nullable=False)
    plan = Column(String(50), server_default='free')
    status = Column(String(20), server_default='active')
    monthly_query_limit = Column(Integer, server_default='10000')
    monthly_index_limit = Column(Integer, server_default='1000')
    max_products = Column(Integer, server_default='5000')
    region = Column(String(32), nullable=False, server_default='us-east-1')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("region <> ''", name='ck_organizations_region'),
    )


class MerchantStore(Base):
    """A tenant-owned storefront or commerce business unit."""
    __tablename__ = 'merchant_stores'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    external_id = Column(String(255))
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, server_default='active')
    settings = Column(JSONB, server_default='{}')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        ForeignKeyConstraint(
            ['organization_id'], ['organizations.id'], ondelete='CASCADE', name='fk_merchant_stores_organization'
        ),
        UniqueConstraint('id', 'organization_id', name='uq_merchant_stores_id_organization'),
        UniqueConstraint('organization_id', 'slug', name='uq_merchant_stores_org_slug'),
        UniqueConstraint('organization_id', 'external_id', name='uq_merchant_stores_org_external_id'),
        Index('idx_merchant_stores_org_status', 'organization_id', 'status'),
    )


class Seller(Base):
    """A seller identity retained for future marketplace catalog isolation."""
    __tablename__ = 'sellers'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    external_id = Column(String(255))
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, server_default='active')
    metadata_json = Column('metadata', JSONB, server_default='{}')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        ForeignKeyConstraint(
            ['organization_id'], ['organizations.id'], ondelete='CASCADE', name='fk_sellers_organization'
        ),
        UniqueConstraint('id', 'organization_id', name='uq_sellers_id_organization'),
        UniqueConstraint('organization_id', 'slug', name='uq_sellers_org_slug'),
        UniqueConstraint('organization_id', 'external_id', name='uq_sellers_org_external_id'),
        Index('idx_sellers_org_status', 'organization_id', 'status'),
    )


class Catalog(Base):
    """A tenant-owned collection of one resource type available to search."""
    __tablename__ = 'catalogs'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    store_id = Column(UUID(as_uuid=True))
    seller_id = Column(UUID(as_uuid=True))
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False)
    resource_type = Column(String(20), nullable=False, server_default='product')
    status = Column(String(20), nullable=False, server_default='active')
    settings = Column(JSONB, server_default='{}')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        ForeignKeyConstraint(
            ['organization_id'], ['organizations.id'], ondelete='CASCADE', name='fk_catalogs_organization'
        ),
        ForeignKeyConstraint(
            ['store_id', 'organization_id'],
            ['merchant_stores.id', 'merchant_stores.organization_id'],
            name='fk_catalogs_store_organization',
        ),
        ForeignKeyConstraint(
            ['seller_id', 'organization_id'],
            ['sellers.id', 'sellers.organization_id'],
            name='fk_catalogs_seller_organization',
        ),
        UniqueConstraint('id', 'organization_id', name='uq_catalogs_id_organization'),
        UniqueConstraint('organization_id', 'slug', name='uq_catalogs_org_slug'),
        CheckConstraint(
            "resource_type IN ('product', 'document', 'asset', 'content')",
            name='ck_catalogs_resource_type',
        ),
        Index('idx_catalogs_org_status', 'organization_id', 'status'),
    )


class CatalogItem(Base):
    """Canonical tenant-scoped record for products and other searchable resources."""
    __tablename__ = 'catalog_items'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    catalog_id = Column(UUID(as_uuid=True), nullable=False)
    seller_id = Column(String(255), index=True)
    parent_item_id = Column(UUID(as_uuid=True))
    external_id = Column(String(512), nullable=False)
    resource_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, server_default='active')
    title = Column(String(500), nullable=False)
    description = Column(Text)
    url = Column(Text)
    brand = Column(String(255))
    category = Column(String(255))
    sub_category = Column(String(255))
    document = Column(JSONB, nullable=False, server_default='{}')
    source_system = Column(String(50), nullable=False, server_default='manual')
    source_version = Column(String(255))
    source_updated_at = Column(DateTime(timezone=True))
    index_version = Column(Integer, nullable=False, server_default='1')
    index_status = Column(String(20), nullable=False, server_default='pending')
    index_error = Column(Text)
    indexed_at = Column(DateTime(timezone=True))
    deleted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        ForeignKeyConstraint(
            ['catalog_id', 'organization_id'],
            ['catalogs.id', 'catalogs.organization_id'],
            ondelete='CASCADE',
            name='fk_catalog_items_catalog_organization',
        ),
        ForeignKeyConstraint(
            ['parent_item_id', 'catalog_id', 'organization_id'],
            ['catalog_items.id', 'catalog_items.catalog_id', 'catalog_items.organization_id'],
            name='fk_catalog_items_parent_catalog_organization',
        ),
        UniqueConstraint('id', 'catalog_id', 'organization_id', name='uq_catalog_items_id_catalog_org'),
        UniqueConstraint(
            'organization_id', 'catalog_id', 'external_id', name='uq_catalog_items_org_catalog_external_id'
        ),
        CheckConstraint(
            "resource_type IN ('product', 'document', 'asset', 'content')",
            name='ck_catalog_items_resource_type',
        ),
        CheckConstraint(
            "index_status IN ('pending', 'processing', 'indexed', 'failed', 'dead')",
            name='ck_catalog_items_index_status',
        ),
        Index('idx_catalog_items_org_catalog_type_status', 'organization_id', 'catalog_id', 'resource_type', 'status'),
        Index('idx_catalog_items_parent', 'parent_item_id'),
        Index('idx_catalog_items_index_status', 'organization_id', 'catalog_id', 'index_status'),
        Index('idx_catalog_items_document', 'document', postgresql_using='gin'),
    )


class CatalogIndexEvent(Base):
    """Durable outbox event for synchronizing a canonical catalog item to search."""
    __tablename__ = 'catalog_index_events'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    catalog_id = Column(UUID(as_uuid=True), nullable=False)
    catalog_item_id = Column(UUID(as_uuid=True), nullable=False)
    item_version = Column(Integer, nullable=False)
    operation = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, server_default='pending')
    attempts = Column(Integer, nullable=False, server_default='0')
    payload = Column(JSONB, nullable=False, server_default='{}')
    error = Column(Text)
    # `available_at` doubles as a retry schedule and a processing lease expiry.
    # A worker that dies after claiming an event therefore cannot strand it forever.
    available_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    processed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        ForeignKeyConstraint(
            ['catalog_item_id', 'catalog_id', 'organization_id'],
            ['catalog_items.id', 'catalog_items.catalog_id', 'catalog_items.organization_id'],
            ondelete='CASCADE',
            name='fk_catalog_index_events_catalog_item',
        ),
        CheckConstraint("operation IN ('upsert', 'delete')", name='ck_catalog_index_events_operation'),
        CheckConstraint(
            "status IN ('pending', 'processing', 'indexed', 'failed', 'dead')",
            name='ck_catalog_index_events_status',
        ),
        Index(
            'idx_catalog_index_events_pending',
            'organization_id',
            'catalog_id',
            'status',
            'available_at',
        ),
        Index('idx_catalog_index_events_item_version', 'catalog_item_id', 'item_version'),
    )


class APIKey(Base):
    """API Keys for tenant authentication (public search / private admin)"""
    __tablename__ = 'api_keys'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    key_prefix = Column(String(12), nullable=False)
    key_hash = Column(String(64), unique=True, nullable=False)
    key_type = Column(String(20), nullable=False)  # 'public_search' | 'private_admin'
    name = Column(String(100))
    scopes = Column(ARRAY(String), server_default='{}')
    rate_limit_per_minute = Column(Integer, server_default='60')
    is_active = Column(Boolean, server_default='true')
    last_used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_api_keys_hash', 'key_hash'),
        Index('idx_api_keys_org', 'organization_id'),
    )


class TenantConfig(Base):
    """Search, UX, and inventory behavior settings for a tenant"""
    __tablename__ = 'tenant_configs'

    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), primary_key=True)
    enable_semantic = Column(Boolean, server_default='true')
    enable_personalization = Column(Boolean, server_default='false')
    enable_image_search = Column(Boolean, server_default='false')
    rrf_keyword_weight = Column(Float, server_default='0.6')
    rrf_vector_weight = Column(Float, server_default='0.4')
    typo_tolerance = Column(Integer, server_default='2')
    searchable_fields = Column(ARRAY(String), server_default='{title,description,brand,category}')
    facet_fields = Column(ARRAY(String), server_default='{brand,category}')
    widget_primary_color = Column(String(7), server_default='#6366f1')
    widget_font_family = Column(String(100), server_default='Inter')
    widget_position = Column(String(20), server_default='center')
    widget_placeholder = Column(Text, server_default='Search products...')
    out_of_stock_behavior = Column(String(20), server_default='demote')  # 'hide' | 'demote' | 'notify'
    webhook_urls = Column(ARRAY(String), server_default='{}')
    allowed_domains = Column(ARRAY(String), server_default='{}')
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PinnedProduct(Base):
    """Merchandising rules to pin specific products to queries"""
    __tablename__ = 'pinned_products'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    query_pattern = Column(String(255), nullable=False)
    product_id = Column(String(100), nullable=False)
    position = Column(Integer, server_default='1')
    is_active = Column(Boolean, server_default='true')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_pinned_org_query', 'organization_id', 'query_pattern'),
    )


class Synonym(Base):
    """Custom synonyms for search queries"""
    __tablename__ = 'synonyms'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    term = Column(String(255), nullable=False)
    synonyms = Column(ARRAY(String), nullable=False)
    is_active = Column(Boolean, server_default='true')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_synonyms_org', 'organization_id'),
    )


class RedirectRule(Base):
    """URL redirects for specific search queries"""
    __tablename__ = 'redirect_rules'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    query_pattern = Column(String(255), nullable=False)
    redirect_url = Column(Text, nullable=False)
    is_active = Column(Boolean, server_default='true')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_redirects_org_query', 'organization_id', 'query_pattern'),
    )


class BoostRule(Base):
    """Boost or bury products by attribute or ID"""
    __tablename__ = 'boost_rules'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    query_pattern = Column(String(255))  # If null, applies globally
    attribute_name = Column(String(255)) # e.g. "brand", "category", or "id"
    attribute_value = Column(String(255))
    boost_factor = Column(Float, nullable=False) # >1 for boost, <1 for bury
    is_active = Column(Boolean, server_default='true')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_boosts_org', 'organization_id'),
    )


class UsageEvent(Base):
    """API usage tracking for billing and rate limiting"""
    __tablename__ = 'usage_events'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    event_type = Column(String(30), nullable=False)  # 'search_query' | 'index_upsert' | 'image_search'
    query_text = Column(Text)
    latency_ms = Column(Integer)
    result_count = Column(Integer)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey('api_keys.id', ondelete='SET NULL'))
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_usage_org_time', 'organization_id', 'created_at'),
    )


class AnalyticsDaily(Base):
    """Aggregated daily analytics for tenant reports"""
    __tablename__ = 'analytics_daily'

    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), primary_key=True)
    date = Column(Date, primary_key=True)
    total_queries = Column(Integer, server_default='0')
    unique_queries = Column(Integer, server_default='0')
    avg_latency_ms = Column(Float, server_default='0')
    zero_result_count = Column(Integer, server_default='0')
    cache_hit_rate = Column(Float, server_default='0')
    top_queries = Column(JSONB, server_default='[]')
    top_zero_result_queries = Column(JSONB, server_default='[]')


class AuditLog(Base):
    """Immutable audit trail for governance and compliance"""
    __tablename__ = 'audit_logs'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    actor_id = Column(String(255), nullable=False)  # User ID or API Key ID
    actor_type = Column(String(50), nullable=False)  # 'user' | 'api_key' | 'system'
    action = Column(String(100), nullable=False)  # e.g., 'catalog.upsert', 'rbac.grant'
    resource_type = Column(String(100), nullable=False)  # 'catalog_item', 'api_key'
    resource_id = Column(String(255), nullable=False)
    payload = Column(JSONB, server_default='{}')
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_audit_org_time', 'organization_id', 'created_at'),
        Index('idx_audit_org_actor', 'organization_id', 'actor_id'),
        Index('idx_audit_org_resource', 'organization_id', 'resource_type', 'resource_id'),
    )
