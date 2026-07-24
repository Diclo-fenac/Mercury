import pytest

from app.domain.tenants.importer import CatalogImporter


class CatalogServiceStub:
    def __init__(self, calls):
        self.calls = calls
        self.outcomes = []

    async def upsert_products(self, organization_id, products):
        self.calls.append("persist")
        return [{**product, "index_event_id": f"event-{product['id']}"} for product in products]

    async def record_index_results(self, outcomes):
        self.calls.append("record")
        self.outcomes.extend(outcomes)


class EmbeddingsStub:
    async def embed_batch(self, texts):
        return [[0.1, 0.2] for _ in texts]


class TypesenseStub:
    def __init__(self, calls):
        self.calls = calls
        self.documents = []

    async def index_documents(self, collection_name, documents):
        self.calls.append("index")
        self.documents.extend(documents)
        return {"success": True, "results": [{"success": True} for _ in documents]}


@pytest.mark.asyncio
async def test_import_persists_before_embedding_and_typesense_indexing():
    calls = []
    catalog_service = CatalogServiceStub(calls)
    typesense = TypesenseStub(calls)
    importer = CatalogImporter(typesense, EmbeddingsStub(), catalog_service)

    result = await importer.import_json(
        "tenant-1",
        [{"id": "sku-1", "name": "Mercury Shoe", "category": "Shoes"}],
    )

    assert result == {"success": True, "total": 1, "indexed": 1, "errors": 0}
    assert calls == ["persist", "index", "record"]
    assert typesense.documents[0]["embedding"] == [0.1, 0.2]
    assert "index_event_id" not in typesense.documents[0]
    assert "catalog_item_id" not in typesense.documents[0]
    assert catalog_service.outcomes == [{"event_id": "event-sku-1", "success": True, "error": None}]
