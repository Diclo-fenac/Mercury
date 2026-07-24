"""p3_audit_rbac

Revision ID: 1e97e0828f95
Revises: 700bc93b06d3
Create Date: 2026-07-23 17:23:05.957216

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '1e97e0828f95'
down_revision: Union[str, Sequence[str], None] = '700bc93b06d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actor_id', sa.String(length=255), nullable=False),
        sa.Column('actor_type', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=255), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name=op.f('fk_audit_logs_organization_id_organizations'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_logs'))
    )
    op.create_index(op.f('idx_audit_org_actor'), 'audit_logs', ['organization_id', 'actor_id'], unique=False)
    op.create_index(op.f('idx_audit_org_resource'), 'audit_logs', ['organization_id', 'resource_type', 'resource_id'], unique=False)
    op.create_index(op.f('idx_audit_org_time'), 'audit_logs', ['organization_id', 'created_at'], unique=False)

    op.add_column('tenant_users', sa.Column('roles', postgresql.ARRAY(sa.String()), server_default='{"user"}', nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('tenant_users', 'roles')

    op.drop_index(op.f('idx_audit_org_time'), table_name='audit_logs')
    op.drop_index(op.f('idx_audit_org_resource'), table_name='audit_logs')
    op.drop_index(op.f('idx_audit_org_actor'), table_name='audit_logs')
    op.drop_table('audit_logs')
