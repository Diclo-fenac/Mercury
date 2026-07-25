"""Retry worker for durable catalog-to-search index events."""
from typing import Any, Dict, List


class CatalogIndexWorker:
    """Replay pending catalog events. Safe across processes through row-level claiming."""

    def __init__(self, catalog_service, embeddings, typesense, tenant_provisioner=None):
        self.catalog_service = catalog_service
        self.embeddings = embeddings
        self.typesense = typesense
        self.tenant_provisioner = tenant_provisioner

    async def run_once(self, limit: int = 100) -> Dict[str, int]:
        events = await self.catalog_service.claim_index_events(limit)
        outcomes: List[Dict[str, Any]] = []
        for event in events:
            event_id = event["event_id"]
            document = event["document"]
            collection = f"tenant_{event['organization_id']}_products"
            try:
                if not self.typesense:
                    raise RuntimeError("Typesense unavailable")
                if event["operation"] == "delete":
                    doc_id = str(event.get("external_id") or (document.get("id") if document else "") or (event.get("payload", {}).get("external_id", "")) or "")
                    succeeded = await self.typesense.delete_document(collection, doc_id)
                    outcomes.append(
                        {
                            "event_id": event_id,
                            "success": succeeded,
                            "error": None if succeeded else "Typesense delete failed",
                        }
                    )
                    continue
                if not await self.typesense.collection_exists(collection):
                    if self.tenant_provisioner:
                        await self.tenant_provisioner.provision_tenant(str(event["organization_id"]))
                    else:
                        schema = {
                            "name": collection,
                            "fields": [
                                {"name": "id", "type": "string"},
                                {"name": "title", "type": "string", "optional": True},
                                {"name": "name", "type": "string", "optional": True},
                                {"name": "brand", "type": "string", "optional": True, "facet": True},
                                {"name": "category", "type": "string", "optional": True, "facet": True},
                                {"name": "sub_category", "type": "string", "optional": True, "facet": True},
                                {"name": "description", "type": "string", "optional": True},
                                {"name": "rating", "type": "float"},
                                {"name": "stock", "type": "bool", "optional": True},
                                {"name": "online_available", "type": "bool", "optional": True},
                                {"name": "selling_price", "type": "float", "optional": True},
                                {"name": "embedding", "type": "float[]", "num_dim": 384, "optional": True},
                                {"name": "image_vector", "type": "float[]", "num_dim": 512, "optional": True},
                            ],
                            "default_sorting_field": "rating"
                        }
                        await self.typesense.create_collection(schema)
                    
                text = " ".join(
                    str(document.get(field, ""))
                    for field in ("title", "name", "description", "brand", "category", "sub_category")
                    if document.get(field)
                )
                vector = await self.embeddings.embed_text(text)
                search_document = {**document, "embedding": vector or [0.0] * 384}
                result = await self.typesense.index_documents(collection, [search_document])
                detail = (result.get("results") or [{}])[0]
                outcomes.append(
                    {
                        "event_id": event_id,
                        "success": bool(detail.get("success", result.get("success"))),
                        "error": detail.get("error") or result.get("error"),
                    }
                )
            except Exception as exc:
                outcomes.append({"event_id": event_id, "success": False, "error": str(exc)})
        await self.catalog_service.record_index_results(outcomes)
        return {
            "claimed": len(events),
            "indexed": sum(outcome["success"] for outcome in outcomes),
            "failed": sum(not outcome["success"] for outcome in outcomes),
        }
