import pytest

from app.domain.catalogs.service import CatalogService


class RepositoryStub:
    async def ensure_default_product_catalog(self, organization_id):
        self.organization_id = organization_id
        return "catalog-1"

    async def upsert_products(self, organization_id, catalog_id, products):
        self.upsert_args = (organization_id, catalog_id, products)
        return products

    async def record_index_results(self, outcomes):
        self.outcomes = outcomes

    async def delete_product(self, organization_id, external_id):
        self.delete_args = (organization_id, external_id)
        return True


@pytest.mark.asyncio
async def test_catalog_service_resolves_default_catalog_before_upsert():
    repository = RepositoryStub()
    service = CatalogService(repository)
    products = [{"id": "sku-1", "title": "Mercury Shoe"}]

    assert await service.upsert_products("tenant-1", products) == products
    assert repository.upsert_args == ("tenant-1", "catalog-1", products)


@pytest.mark.asyncio
async def test_catalog_service_deletes_through_canonical_repository():
    repository = RepositoryStub()
    service = CatalogService(repository)

    assert await service.delete_product("tenant-1", "sku-1") is True
    assert repository.delete_args == ("tenant-1", "sku-1")
