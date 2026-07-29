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
        if not events:
            return {"claimed": 0, "indexed": 0, "failed": 0}
            
        outcomes: List[Dict[str, Any]] = []
        
        # Group events by collection for bulk operations
        from collections import defaultdict
        import asyncio
        
        deletes = []
        upsert_events = []
        
        for event in events:
            if event["operation"] == "delete":
                deletes.append(event)
            else:
                upsert_events.append(event)
                
        # 1. Process Deletes
        for event in deletes:
            event_id = event["event_id"]
            document = event.get("document", {})
            collection = f"tenant_{event['organization_id']}_products"
            try:
                if not self.typesense:
                    raise RuntimeError("Typesense unavailable")
                doc_id = str(event.get("external_id") or (document.get("id") if document else "") or (event.get("payload", {}).get("external_id", "")) or "")
                succeeded = await self.typesense.delete_document(collection, doc_id)
                outcomes.append({
                    "event_id": event_id,
                    "success": succeeded,
                    "error": None if succeeded else "Typesense delete failed",
                })
            except Exception as exc:
                outcomes.append({"event_id": event_id, "success": False, "error": str(exc)})
                
        # 2. Process Upserts in Bulk
        if upsert_events:
            upserts_by_collection = defaultdict(list)
            
            # Prepare embeddings concurrently
            async def prepare_doc(event):
                try:
                    document = event["document"]
                    collection = f"tenant_{event['organization_id']}_products"
                    text = " ".join(
                        str(document.get(field, ""))
                        for field in ("title", "name", "description", "brand", "category", "sub_category")
                        if document.get(field)
                    )
                    vector = await self.embeddings.embed_text(text) if text else [0.0] * 384
                    search_document = {**document, "embedding": vector or [0.0] * 384}
                    return event, collection, search_document, None
                except Exception as e:
                    return event, None, None, str(e)

            prepared_docs = await asyncio.gather(*(prepare_doc(evt) for evt in upsert_events))
            
            for event, collection, doc, error in prepared_docs:
                if error:
                    outcomes.append({"event_id": event["event_id"], "success": False, "error": error})
                else:
                    upserts_by_collection[collection].append((event, doc))
                    
            # Ensure collections exist and bulk insert
            for collection, items in upserts_by_collection.items():
                if not items:
                    continue
                try:
                    if not self.typesense:
                        raise RuntimeError("Typesense unavailable")
                        
                    # Create collection if missing
                    if not await self.typesense.collection_exists(collection):
                        if self.tenant_provisioner:
                            # Use first event's org_id
                            await self.tenant_provisioner.provision_tenant(str(items[0][0]["organization_id"]))
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
                            
                    # Bulk insert
                    documents_to_insert = [doc for _, doc in items]
                    result = await self.typesense.index_documents(collection, documents_to_insert)
                    
                    bulk_results = result.get("results", [])
                    success_overall = result.get("success", False)
                    
                    # Map results back to events
                    for i, (event, doc) in enumerate(items):
                        if i < len(bulk_results):
                            detail = bulk_results[i]
                            outcomes.append({
                                "event_id": event["event_id"],
                                "success": bool(detail.get("success", success_overall)),
                                "error": detail.get("error") or result.get("error"),
                            })
                        else:
                            outcomes.append({
                                "event_id": event["event_id"],
                                "success": success_overall,
                                "error": result.get("error") if not success_overall else None,
                            })
                            
                except Exception as exc:
                    for event, _ in items:
                        outcomes.append({"event_id": event["event_id"], "success": False, "error": str(exc)})
                        
        # 3. Record outcomes
        await self.catalog_service.record_index_results(outcomes)
        
        return {
            "claimed": len(events),
            "indexed": sum(outcome["success"] for outcome in outcomes),
            "failed": sum(not outcome["success"] for outcome in outcomes),
        }
