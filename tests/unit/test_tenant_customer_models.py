from sqlalchemy import ForeignKeyConstraint

from app.infrastructure.db.models import (
    TenantActivity,
    TenantConversation,
    TenantMessage,
    TenantUser,
)


def _foreign_key_names(model):
    return {
        constraint.name
        for constraint in model.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }


def test_customer_identity_is_composite_and_tenant_local():
    primary_key = {column.name for column in TenantUser.__table__.primary_key.columns}

    assert primary_key == {"organization_id", "id"}
    assert "idx_tenant_users_org_email" in {index.name for index in TenantUser.__table__.indexes}


def test_conversations_and_messages_cannot_cross_tenant_or_user_boundary():
    assert {"organization_id", "id"} == {
        column.name for column in TenantConversation.__table__.primary_key.columns
    }
    assert "fk_tenant_conversations_user" in _foreign_key_names(TenantConversation)
    assert "fk_tenant_messages_conversation" in _foreign_key_names(TenantMessage)
    assert "fk_tenant_messages_user" in _foreign_key_names(TenantMessage)


def test_activity_is_bound_to_tenant_local_customer():
    assert "fk_tenant_activities_user" in _foreign_key_names(TenantActivity)
    assert "idx_tenant_activities_org_user_created" in {
        index.name for index in TenantActivity.__table__.indexes
    }
