from dataclasses import dataclass

import pytest

from app.addons.search.hybrid import HybridSearch
from app.core.security.context import tenant_context_var


@dataclass
class Tenant:
    organization_id: str = "tenant-1"
    collection_name: str = "tenant_tenant-1_products"
    seller_id: str = None
    config: dict = None


class EmbeddingsStub:
    async def embed_query(self, query):
        assert query == "running shoe"
        return [0.1, 0.2]


class TypesenseStub:
    def __init__(self):
        self.calls = []

    async def search(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get("vector_query"):
            return {
                "success": True,
                "found": 2,
                "documents": [
                    {"id": "sku-2", "_typesense": {"vector_distance": 0.1}},
                    {"id": "sku-1", "_typesense": {"vector_distance": 0.2}},
                ],
                "facet_counts": [],
                "search_time_ms": 3,
            }
        return {
            "success": True,
            "found": 2,
            "documents": [
                {"id": "sku-1", "_typesense": {"text_match": 100}},
                {"id": "sku-2", "_typesense": {"text_match": 80}},
            ],
            "facet_counts": [],
            "search_time_ms": 2,
        }


class DatabaseStub:
    async def get_products_by_ids(self, organization_id, ids):
        assert organization_id == "tenant-1"
        return {
            "sku-1": {"id": "sku-1", "title": "Canonical Shoe"},
            "sku-2": {"id": "sku-2", "title": "Canonical Runner"},
        }

    async def search_products(self, *args, **kwargs):
        raise AssertionError("Typesense results should be rehydrated, not fallback")


@pytest.mark.asyncio
async def test_hybrid_retrieval_filters_then_fuses_and_rehydrates_canonical_rows():
    typesense = TypesenseStub()
    search = HybridSearch(typesense, DatabaseStub(), EmbeddingsStub())
    token = tenant_context_var.set(Tenant())
    try:
        result = await search.search_with_metadata(
            query="running shoe",
            filters={"category": ["Shoes"], "stock_only": True},
            limit=1,
            offset=1,
            collection="tenant_tenant-1_products",
        )
    finally:
        tenant_context_var.reset(token)

    assert result["retrieval"] == "rrf"
    assert result["total"] == 2
    assert result["documents"][0]["id"] == "sku-2"
    assert result["documents"][0]["_retrieval"]["ranks"] == {
        "keyword": {"rank": 2, "text_match": 80, "vector_distance": None},
        "semantic": {"rank": 1, "text_match": None, "vector_distance": 0.1},
    }
    assert len(typesense.calls) == 2
    assert all(call["filter_by"] == "(category:=`Shoes`) && stock:=true" for call in typesense.calls)


@pytest.mark.asyncio
async def test_keyword_only_tenant_skips_embedding_and_vector_search():
    typesense = TypesenseStub()
    search = HybridSearch(typesense, DatabaseStub(), EmbeddingsStub())
    token = tenant_context_var.set(Tenant(config={"enable_semantic": False}))
    try:
        result = await search.search_with_metadata(
            query="running shoe",
            limit=1,
            collection="tenant_tenant-1_products",
        )
    finally:
        tenant_context_var.reset(token)

    assert result["retrieval"] == "keyword"
    assert len(typesense.calls) == 1
    assert "vector_query" not in typesense.calls[0]


def test_typesense_filter_compiles_only_known_fields_and_quotes_values():
    search = HybridSearch(None, None)

    compiled = search._build_typesense_filter(
        {"brand": ["ACME` || stock:=false"], "ignored": "not-a-filter"}
    )

    assert compiled == "(brand:=`ACME\\` || stock:=false`)"
