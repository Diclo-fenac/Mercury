"""Application service for canonical catalog writes and index outcomes."""
from typing import Any, Dict, Iterable, List


class CatalogService:
    """Coordinates tenant catalog provisioning with persistence and index state."""

    def __init__(self, repository):
        self.repository = repository

    async def upsert_products(self, organization_id: str, products: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        catalog_id = await self.repository.ensure_default_product_catalog(organization_id)
        return await self.repository.upsert_products(organization_id, catalog_id, list(products))

    async def record_index_results(self, outcomes: Iterable[Dict[str, Any]]) -> None:
        await self.repository.record_index_results(list(outcomes))

    async def delete_product(self, organization_id: str, external_id: str) -> bool:
        return await self.repository.delete_product(organization_id, external_id)

    async def claim_index_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        return await self.repository.claim_index_events(limit)
