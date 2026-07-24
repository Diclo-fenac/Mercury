from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from app.domain.tenants.models import (
    Catalog,
    CatalogIndexEvent,
    CatalogItem,
    MerchantStore,
    Organization,
    Seller,
)


def _constraint_names(table, constraint_type):
    return {constraint.name for constraint in table.constraints if isinstance(constraint, constraint_type)}


def test_organization_has_a_non_nullable_deployment_region():
    region = Organization.__table__.c.region

    assert region.nullable is False
    assert region.server_default is not None


def test_catalog_ownership_models_are_tenant_scoped():
    assert MerchantStore.__table__.c.organization_id.nullable is False
    assert Seller.__table__.c.organization_id.nullable is False
    assert Catalog.__table__.c.organization_id.nullable is False

    catalog_fks = {
        constraint.name
        for constraint in Catalog.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }
    assert "fk_catalogs_organization" in catalog_fks
    assert "fk_catalogs_store_organization" in catalog_fks
    assert "fk_catalogs_seller_organization" in catalog_fks


def test_catalog_items_allow_duplicate_external_ids_only_across_catalogs():
    names = _constraint_names(CatalogItem.__table__, UniqueConstraint)

    assert "uq_catalog_items_org_catalog_external_id" in names
    assert CatalogItem.__table__.c.external_id.nullable is False
    assert CatalogItem.__table__.c.organization_id.nullable is False
    assert CatalogItem.__table__.c.catalog_id.nullable is False


def test_catalog_item_parent_variant_is_constrained_to_the_same_catalog_and_tenant():
    foreign_keys = {
        constraint.name
        for constraint in CatalogItem.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }

    assert "fk_catalog_items_catalog_organization" in foreign_keys
    assert "fk_catalog_items_parent_catalog_organization" in foreign_keys
    assert CatalogItem.__table__.c.parent_item_id.nullable is True


def test_catalog_and_item_resource_types_are_constrained():
    catalog_checks = _constraint_names(Catalog.__table__, CheckConstraint)
    item_checks = _constraint_names(CatalogItem.__table__, CheckConstraint)

    assert "ck_catalogs_resource_type" in catalog_checks
    assert "ck_catalog_items_resource_type" in item_checks


def test_catalog_items_have_tenant_first_lookup_indexes():
    index_names = {index.name for index in CatalogItem.__table__.indexes}

    assert "idx_catalog_items_org_catalog_type_status" in index_names
    assert "idx_catalog_items_parent" in index_names


def test_catalog_items_track_durable_index_state():
    assert CatalogItem.__table__.c.index_version.nullable is False
    assert CatalogItem.__table__.c.index_status.nullable is False
    assert "idx_catalog_items_index_status" in {index.name for index in CatalogItem.__table__.indexes}


def test_catalog_index_events_are_tenant_and_item_scoped():
    foreign_keys = {
        constraint.name
        for constraint in CatalogIndexEvent.__table__.constraints
        if isinstance(constraint, ForeignKeyConstraint)
    }
    checks = _constraint_names(CatalogIndexEvent.__table__, CheckConstraint)

    assert "fk_catalog_index_events_catalog_item" in foreign_keys
    assert "ck_catalog_index_events_operation" in checks
    assert "ck_catalog_index_events_status" in checks
    assert "idx_catalog_index_events_pending" in {
        index.name for index in CatalogIndexEvent.__table__.indexes
    }
