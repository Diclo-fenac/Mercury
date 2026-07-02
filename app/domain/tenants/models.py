"""
SQLAlchemy Models for Multi-Tenancy
"""
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


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


class UsageEvent(Base):
    """API usage tracking for billing and rate limiting"""
    __tablename__ = 'usage_events'

    id = Column(Integer, primary_key=True, autoincrement=True)
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
