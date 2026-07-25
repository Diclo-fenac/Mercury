import pytest

from app.infrastructure.catalog.worker import CatalogIndexWorker


class CatalogServiceStub:
    def __init__(self, events):
        self.events = events
        self.outcomes = []

    async def claim_index_events(self, limit):
        assert limit == 100
        return self.events

    async def record_index_results(self, outcomes):
        self.outcomes = outcomes


class EmbeddingsStub:
    async def embed_text(self, text):
        assert "Mercury Shoe" in text
        return [0.1, 0.2]


class TypesenseStub:
    def __init__(self):
        self.indexed = []
        self.deleted = []

    async def collection_exists(self, collection_name: str) -> bool:
        return True
        
    async def create_collection(self, schema: dict) -> bool:
        return True

    async def index_documents(self, collection, documents):
        self.indexed.append((collection, documents))
        return {"success": True, "results": [{"success": True}]}

    async def delete_document(self, collection, document_id):
        self.deleted.append((collection, document_id))
        return True


@pytest.mark.asyncio
async def test_worker_replays_upsert_event_and_records_success():
    catalog = CatalogServiceStub(
        [
            {
                "event_id": "event-1",
                "organization_id": "tenant-1",
                "operation": "upsert",
                "document": {"id": "sku-1", "title": "Mercury Shoe", "description": "Running"},
            }
        ]
    )
    typesense = TypesenseStub()

    result = await CatalogIndexWorker(catalog, EmbeddingsStub(), typesense).run_once()

    assert result == {"claimed": 1, "indexed": 1, "failed": 0}
    assert typesense.indexed == [
        (
            "tenant_tenant-1_products",
            [{"id": "sku-1", "title": "Mercury Shoe", "description": "Running", "embedding": [0.1, 0.2]}],
        )
    ]
    assert catalog.outcomes == [{"event_id": "event-1", "success": True, "error": None}]


@pytest.mark.asyncio
async def test_worker_replays_delete_event_without_embedding():
    catalog = CatalogServiceStub(
        [
            {
                "event_id": "event-1",
                "organization_id": "tenant-1",
                "operation": "delete",
                "document": {"id": "sku-1", "title": "Mercury Shoe"},
            }
        ]
    )
    typesense = TypesenseStub()

    result = await CatalogIndexWorker(catalog, EmbeddingsStub(), typesense).run_once()

    assert result == {"claimed": 1, "indexed": 1, "failed": 0}
    assert typesense.deleted == [("tenant_tenant-1_products", "sku-1")]
    assert catalog.outcomes == [{"event_id": "event-1", "success": True, "error": None}]


@pytest.mark.asyncio
async def test_worker_marks_event_failed_when_typesense_is_unavailable():
    catalog = CatalogServiceStub(
        [
            {
                "event_id": "event-1",
                "organization_id": "tenant-1",
                "operation": "upsert",
                "document": {"id": "sku-1", "title": "Mercury Shoe"},
            }
        ]
    )

    result = await CatalogIndexWorker(catalog, EmbeddingsStub(), None).run_once()

    assert result == {"claimed": 1, "indexed": 0, "failed": 1}
    assert catalog.outcomes == [
        {"event_id": "event-1", "success": False, "error": "Typesense unavailable"}
    ]
