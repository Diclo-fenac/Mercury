from dataclasses import dataclass

import pytest

from app.orchestrators.search_orchestrator import SearchOrchestrator


@dataclass
class Tenant:
    organization_id: str = "tenant-a"
    collection_name: str = "tenant_a_products"
    config: dict = None

    def __post_init__(self):
        if self.config is None:
            self.config = {"enable_personalization": False, "out_of_stock_behavior": "demote"}


class MemorySearchCache:
    def __init__(self):
        self.values = {}
        self.requested_keys = []

    async def get_tenant_namespace_revision(self, tenant_id, namespace):
        assert namespace == "search"
        return 7

    async def get_json(self, key):
        self.requested_keys.append(key)
        return self.values.get(key)

    async def set_json(self, key, value, ttl):
        self.values[key] = value
        return True


class SearchStub:
    def __init__(self):
        self.calls = 0

    async def search_with_metadata(self, query, filters, limit, collection, **kwargs):
        self.calls += 1
        return {
            "documents": [{"id": str(self.calls), "brand": "Mercury", "category": "Shoes"}],
            "total": 1,
            "facets": [],
            "fallback_used": False,
            "retrieval": "rrf",
        }


class EmptySuggestionsService:
    async def get_suggestions(self, query, limit, collection):
        return []


@pytest.mark.asyncio
async def test_search_cache_includes_page_and_counts_every_lookup():
    cache = MemorySearchCache()
    search = SearchStub()
    orchestrator = SearchOrchestrator(search=search, personalization=None, cache=cache)
    tenant = Tenant()

    await orchestrator.handle("shoes", "user-1", limit=10, offset=0, tenant_context=tenant)
    await orchestrator.handle("shoes", "user-1", limit=10, offset=0, tenant_context=tenant)
    await orchestrator.handle("shoes", "user-1", limit=10, offset=10, tenant_context=tenant)

    assert search.calls == 2
    assert cache.requested_keys[0] == cache.requested_keys[1]
    assert cache.requested_keys[0] != cache.requested_keys[2]
    assert orchestrator._cache_hits == 1
    assert orchestrator._cache_total == 3


@pytest.mark.asyncio
async def test_empty_suggestion_service_falls_back_to_non_empty_suggestions():
    orchestrator = SearchOrchestrator(
        search=None,
        personalization=None,
        cache=None,
        suggestions_service=EmptySuggestionsService(),
    )

    result = await orchestrator.get_suggestions("lap", limit=5, tenant_context=Tenant())

    assert result == {
        "success": True,
        "suggestions": [
            "lap deals",
            "lap reviews",
            "best lap",
            "cheap lap",
            "lap sale",
        ],
    }
