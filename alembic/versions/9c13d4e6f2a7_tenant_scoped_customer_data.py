"""tenant scoped customer data

Revision ID: 9c13d4e6f2a7
Revises: 8b02c3d5e9f1
Create Date: 2026-07-23 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = '9c13d4e6f2a7'
down_revision: Union[str, Sequence[str], None] = '8b02c3d5e9f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create tenant-local customer, conversation, message, and activity tables.

    Legacy global tables stay intact for non-destructive rollout, but application paths
    move to these tables so equal external user IDs cannot cross tenant boundaries.
    """
    op.create_table(
        'tenant_users',
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('gender', sa.String(length=50), nullable=True),
        sa.Column('preferences', postgresql.JSONB(), nullable=True),
        sa.Column('behavior', postgresql.JSONB(), nullable=True),
        sa.Column('health', postgresql.JSONB(), nullable=True),
        sa.Column('location', postgresql.JSONB(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('organization_id', 'id'),
    )
    op.create_index('idx_tenant_users_org_email', 'tenant_users', ['organization_id', 'email'])
    op.create_index(
        'idx_tenant_users_org_preferences', 'tenant_users', ['preferences'], postgresql_using='gin'
    )
    op.create_index(
        'idx_tenant_users_org_behavior', 'tenant_users', ['behavior'], postgresql_using='gin'
    )

    op.create_table(
        'tenant_conversations',
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('channel', sa.String(length=32), server_default='rest', nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('message_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['organization_id', 'user_id'],
            ['tenant_users.organization_id', 'tenant_users.id'],
            ondelete='CASCADE',
            name='fk_tenant_conversations_user',
        ),
        sa.PrimaryKeyConstraint('organization_id', 'id'),
    )
    op.create_index(
        'idx_tenant_conversations_org_user_created',
        'tenant_conversations',
        ['organization_id', 'user_id', 'created_at'],
    )
    op.create_index(
        'idx_tenant_conversations_org_last_message', 'tenant_conversations', ['organization_id', 'last_message_at']
    )

    op.create_table(
        'tenant_messages',
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('conversation_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['organization_id', 'conversation_id'],
            ['tenant_conversations.organization_id', 'tenant_conversations.id'],
            ondelete='CASCADE',
            name='fk_tenant_messages_conversation',
        ),
        sa.ForeignKeyConstraint(
            ['organization_id', 'user_id'],
            ['tenant_users.organization_id', 'tenant_users.id'],
            ondelete='CASCADE',
            name='fk_tenant_messages_user',
        ),
        sa.PrimaryKeyConstraint('organization_id', 'id'),
    )
    op.create_index(
        'idx_tenant_messages_org_conversation_created',
        'tenant_messages',
        ['organization_id', 'conversation_id', 'created_at'],
    )

    op.create_table(
        'tenant_activities',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('activity_type', sa.String(length=100), nullable=False),
        sa.Column('data', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['organization_id', 'user_id'],
            ['tenant_users.organization_id', 'tenant_users.id'],
            ondelete='CASCADE',
            name='fk_tenant_activities_user',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'idx_tenant_activities_org_user_created',
        'tenant_activities',
        ['organization_id', 'user_id', 'created_at'],
    )
    op.create_index(
        'idx_tenant_activities_org_type_created',
        'tenant_activities',
        ['organization_id', 'activity_type', 'created_at'],
    )


def downgrade() -> None:
    op.drop_index('idx_tenant_activities_org_type_created', table_name='tenant_activities')
    op.drop_index('idx_tenant_activities_org_user_created', table_name='tenant_activities')
    op.drop_table('tenant_activities')
    op.drop_index('idx_tenant_messages_org_conversation_created', table_name='tenant_messages')
    op.drop_table('tenant_messages')
    op.drop_index('idx_tenant_conversations_org_last_message', table_name='tenant_conversations')
    op.drop_index('idx_tenant_conversations_org_user_created', table_name='tenant_conversations')
    op.drop_table('tenant_conversations')
    op.drop_index('idx_tenant_users_org_behavior', table_name='tenant_users')
    op.drop_index('idx_tenant_users_org_preferences', table_name='tenant_users')
    op.drop_index('idx_tenant_users_org_email', table_name='tenant_users')
    op.drop_table('tenant_users')
