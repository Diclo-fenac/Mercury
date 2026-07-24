"""Retry worker for durable catalog-to-search index events."""
from typing import Any, Dict, List


class CatalogIndexWorker:
    """Replay pending catalog events. Safe across processes through row-level claiming."""

    def __init__(self, catalog_service, embeddings, typesense):
        self.catalog_service = catalog_service
        self.embeddings = embeddings
        self.typesense = typesense

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
                    succeeded = await self.typesense.delete_document(collection, str(document["id"]))
                    outcomes.append(
                        {
                            "event_id": event_id,
                            "success": succeeded,
                            "error": None if succeeded else "Typesense delete failed",
                        }
                    )
                    continue
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
