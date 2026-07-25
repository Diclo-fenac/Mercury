"""
SQLAlchemy Models
PostgreSQL tables with JSONB columns
"""

import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
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
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class TenantUser(Base):
    """Customer profile isolated by organization; legacy ``users`` remains read-disabled."""
    __tablename__ = 'tenant_users'

    organization_id = Column(
        UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), primary_key=True
    )
    id = Column(String(255), primary_key=True)
    seller_id = Column(String(255), index=True)
    email = Column(String(255))
    name = Column(String(255))
    gender = Column(String(50))
    roles = Column(ARRAY(String), server_default='{"user"}')
    has_consented_to_personalization = Column(Boolean, server_default='false')
    preferences = Column(JSONB)
    behavior = Column(JSONB)
    health = Column(JSONB)
    location = Column(JSONB)
    extra_data = Column('metadata', JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        Index('idx_tenant_users_org_email', 'organization_id', 'email'),
        Index('idx_tenant_users_org_preferences', 'preferences', postgresql_using='gin'),
        Index('idx_tenant_users_org_behavior', 'behavior', postgresql_using='gin'),
    )


class TenantConversation(Base):
    """Conversation scoped to one organization and one tenant-local user."""
    __tablename__ = 'tenant_conversations'

    organization_id = Column(
        UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), primary_key=True
    )
    id = Column(String(255), primary_key=True)
    seller_id = Column(String(255), index=True)
    user_id = Column(String(255), nullable=False)
    channel = Column(String(32), nullable=False, server_default='rest')
    title = Column(String(500))
    extra_data = Column('metadata', JSONB)
    message_count = Column(Integer, nullable=False, server_default='0')
    last_message_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        ForeignKeyConstraint(
            ['organization_id', 'user_id'],
            ['tenant_users.organization_id', 'tenant_users.id'],
            ondelete='CASCADE',
            name='fk_tenant_conversations_user',
        ),
        Index('idx_tenant_conversations_org_user_created', 'organization_id', 'user_id', 'created_at'),
        Index('idx_tenant_conversations_org_last_message', 'organization_id', 'last_message_at'),
    )


class TenantMessage(Base):
    """Conversation message with tenant and ownership foreign-key enforcement."""
    __tablename__ = 'tenant_messages'

    organization_id = Column(
        UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), primary_key=True
    )
    id = Column(String(255), primary_key=True)
    conversation_id = Column(String(255), nullable=False)
    user_id = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    extra_data = Column('metadata', JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        ForeignKeyConstraint(
            ['organization_id', 'conversation_id'],
            ['tenant_conversations.organization_id', 'tenant_conversations.id'],
            ondelete='CASCADE',
            name='fk_tenant_messages_conversation',
        ),
        ForeignKeyConstraint(
            ['organization_id', 'user_id'],
            ['tenant_users.organization_id', 'tenant_users.id'],
            ondelete='CASCADE',
            name='fk_tenant_messages_user',
        ),
        Index('idx_tenant_messages_org_conversation_created', 'organization_id', 'conversation_id', 'created_at'),
    )


class TenantActivity(Base):
    """Tenant-scoped behavior signal. Never mixes user behavior across merchants."""
    __tablename__ = 'tenant_activities'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    seller_id = Column(String(255), index=True)
    user_id = Column(String(255), nullable=False)
    activity_type = Column(String(100), nullable=False)
    data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        ForeignKeyConstraint(
            ['organization_id', 'user_id'],
            ['tenant_users.organization_id', 'tenant_users.id'],
            ondelete='CASCADE',
            name='fk_tenant_activities_user',
        ),
        Index('idx_tenant_activities_org_user_created', 'organization_id', 'user_id', 'created_at'),
        Index('idx_tenant_activities_org_type_created', 'organization_id', 'activity_type', 'created_at'),
    )

class CatalogIntegration(Base):
    """Catalog integration settings and state per organization"""
    __tablename__ = 'catalog_integrations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)

    integration_type = Column(String(50), nullable=False)  # csv, webhook, shopify

    # JSONB for credentials/configuration (e.g., webhook url, api keys, mapping config)
    config = Column(JSONB, nullable=False, server_default='{}')

    # State tracking
    last_sync_at = Column(DateTime(timezone=True))
    sync_status = Column(String(50))  # pending, running, success, error
    last_error = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_catalog_integrations_org', 'organization_id'),
    )


class MerchandisingRule(Base):
    """Merchandising rules for pinning and hiding specific products per query"""
    __tablename__ = 'merchandising_rules'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    
    query_exact_match = Column(String(255), nullable=False)
    
    # JSONB arrays of Product IDs
    pinned_items = Column(JSONB, nullable=False, server_default='[]')
    hidden_items = Column(JSONB, nullable=False, server_default='[]')
    
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('organization_id', 'query_exact_match', name='uix_org_query'),
        Index('idx_merchandising_org_query', 'organization_id', 'query_exact_match'),
    )
