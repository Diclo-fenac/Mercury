"""
Catalog Worker - Change Data Capture & Background Indexing
Implements Blue/Green index swapping for zero-downtime updates.
"""
import time
from typing import Any, Dict, List

from app.infrastructure.db.postgres import PostgresClient
from app.infrastructure.search.typesense import TypesenseClient
from app.utils.logger import get_logger

logger = get_logger("catalog_worker")

class CatalogWorker:
    def __init__(self, typesense: TypesenseClient, db: PostgresClient):
        self.typesense = typesense
        self.db = db

    async def reindex_catalog(
        self,
        tenant_id: str,
        collection_name: str,
        schema: Dict[str, Any],
        documents: List[Dict[str, Any]]
    ):
        """
        Performs atomic blue/green swap indexing.
        1. Creates new shadow collection
        2. Indexes documents into shadow collection
        3. Swaps alias to point to shadow collection
        4. Drops old collection
        """
        version = int(time.time())
        shadow_collection = f"{collection_name}_v{version}"

        logger.info(f"[{tenant_id}] Starting atomic re-index. Shadow collection: {shadow_collection}")

        try:
            # 1. Create shadow collection
            shadow_schema = schema.copy()
            shadow_schema["name"] = shadow_collection

            # Using Typesense client directly (assuming self.typesense.client is the raw client)
            await self.typesense.client.collections.create(shadow_schema)

            # 2. Index documents
            if documents:
                # Use batch import
                await self.typesense.client.collections[shadow_collection].documents.import_(
                    documents, {"action": "upsert"}
                )

            # 3. Swap alias
            old_collection_name = None
            try:
                alias_info = await self.typesense.client.aliases[collection_name].retrieve()
                old_collection_name = alias_info.get("collection_name")
            except Exception:
                # Alias might not exist yet
                pass

            await self.typesense.client.aliases.upsert(
                collection_name, {"collection_name": shadow_collection}
            )
            logger.info(f"[{tenant_id}] Successfully aliased {collection_name} to {shadow_collection}")

            # 4. Drop old collection
            if old_collection_name and old_collection_name != shadow_collection:
                try:
                    await self.typesense.client.collections[old_collection_name].delete()
                    logger.info(f"[{tenant_id}] Dropped old collection {old_collection_name}")
                except Exception as e:
                    logger.warning(f"[{tenant_id}] Failed to drop old collection {old_collection_name}: {e}")

            return {"success": True, "shadow_collection": shadow_collection}
        except Exception as e:
            logger.error(f"[{tenant_id}] Re-indexing failed: {e}")
            try:
                await self.typesense.client.collections[shadow_collection].delete()
            except Exception:
                pass
            raise

async def process_webhook_ingestion(org_id: str, source_id: str, payload: dict, container: Any):
    """
    Background task to process a webhook payload and push data to Typesense.
    """
    logger.info(f"Processing webhook for org {org_id} source {source_id}")
    
    # In a real app, this would use a mapping. For v1, we assume a simple 'products' array.
    products = payload.get("products", [])
    if not products:
        logger.warning("No products found in webhook payload")
        return

    # Extract db and typesense from container
    db_session = container.get("db_session")
    typesense = container.get("typesense")
    
    if not typesense or not db_session:
        logger.error("Dependencies not found in container")
        return
        
    try:
        # 1. Upsert into Canonical Postgres DB (CatalogItem)
        import uuid

        from sqlalchemy import func
        from sqlalchemy.dialects.postgresql import insert

        from app.domain.tenants.models import CatalogItem
        
        async with db_session() as session:
            # For simplicity in v1, we assume a default catalog id or we just don't strictly enforce catalog_id if it's not required, 
            # wait, catalog_id is required in CatalogItem. Let's find or create a catalog.
            from sqlalchemy import select, update

            from app.domain.tenants.models import Catalog
            
            org_uuid = uuid.UUID(org_id)
            
            # Get or create default catalog
            result = await session.execute(select(Catalog).where(Catalog.organization_id == org_uuid).limit(1))
            catalog = result.scalar_one_or_none()
            if not catalog:
                catalog = Catalog(organization_id=org_uuid, name="Default Catalog", slug="default", resource_type="product")
                session.add(catalog)
                await session.flush()
                
            # Fetch mapping config
            from app.infrastructure.db.models import CatalogIntegration
            source_uuid = uuid.UUID(source_id)
            integration_result = await session.execute(
                select(CatalogIntegration).where(CatalogIntegration.id == source_uuid).limit(1)
            )
            integration = integration_result.scalar_one_or_none()
            field_mapping = {}
            if integration and integration.config:
                field_mapping = integration.config.get("field_mapping", {})

            from app.domain.tenants.models import CatalogIndexEvent

            deleted_ids = payload.get("deleted_product_ids", [])
            indexed_count = 0
            failed_count = 0
            deleted_count = 0
            
            for del_id in deleted_ids:
                del_id_str = str(del_id)
                # Soft delete in Postgres
                stmt = update(CatalogItem).where(
                    CatalogItem.organization_id == org_uuid,
                    CatalogItem.catalog_id == catalog.id,
                    CatalogItem.external_id == del_id_str
                ).values(deleted_at=func.now()).returning(CatalogItem.id)
                result = await session.execute(stmt)
                item_id = result.scalar_one_or_none()

                if item_id:
                    # Write to outbox
                    event = CatalogIndexEvent(
                        organization_id=org_uuid,
                        catalog_id=catalog.id,
                        catalog_item_id=item_id,
                        item_version=1,
                        operation='delete',
                        payload={'id': del_id_str}
                    )
                    session.add(event)
                    deleted_count += 1

            for p in products:
                try:
                    # Dynamic mapping with fallbacks
                    id_field = field_mapping.get("id") or "id"
                    title_field = field_mapping.get("title") or "title"
                    desc_field = field_mapping.get("description") or "description"
                    cat_field = field_mapping.get("category") or "category"
                    brand_field = field_mapping.get("brand") or "brand"
                    price_field = field_mapping.get("price") or "price"

                    doc_id = str(p.get(id_field) or p.get("sku") or p.get("id", ""))
                    if not doc_id:
                        continue
                    
                    title = str(p.get(title_field) or p.get("name") or p.get("title", ""))
                    description = str(p.get(desc_field, ""))
                    category = str(p.get(cat_field, ""))
                    brand = str(p.get(brand_field, ""))
                    price = float(p.get(price_field) or p.get("cost") or p.get("price") or 0.0)
                    
                    doc_json = {
                        "price": {"selling": price},
                        "stock": True,
                        "online_available": True
                    }
                    
                    stmt = insert(CatalogItem).values(
                        organization_id=org_uuid,
                        catalog_id=catalog.id,
                        external_id=doc_id,
                        resource_type="product",
                        status="active",
                        title=title,
                        description=description,
                        category=category,
                        brand=brand,
                        document=doc_json
                    )
                    
                    stmt = stmt.on_conflict_do_update(
                        index_elements=['organization_id', 'catalog_id', 'external_id'],
                        set_={
                            'title': title,
                            'description': description,
                            'category': category,
                            'brand': brand,
                            'document': doc_json,
                            'updated_at': func.now(),
                            'deleted_at': None # Restore if soft-deleted
                        }
                    ).returning(CatalogItem.id)
                    
                    result = await session.execute(stmt)
                    item_id = result.scalar_one()
                    
                    search_doc = {
                        "id": doc_id,
                        "title": title,
                        "description": description,
                        "category": category,
                        "brand": brand,
                        "selling_price": price,
                        "stock": True
                    }
                    
                    event = CatalogIndexEvent(
                        organization_id=org_uuid,
                        catalog_id=catalog.id,
                        catalog_item_id=item_id,
                        item_version=1,
                        operation='upsert',
                        payload=search_doc
                    )
                    session.add(event)
                    indexed_count += 1
                    
                except Exception as parse_exc:
                    logger.error(f"Failed to parse product {p}: {parse_exc}")
                    failed_count += 1
                    if integration:
                        integration_config = dict(integration.config or {})
                        integration_config["last_error"] = str(parse_exc)
                        integration.config = integration_config
                        
                    # Publish error event to dashboard
                    try:
                        from app.services.realtime import get_realtime_service
                        realtime = get_realtime_service()
                        import asyncio
                        asyncio.create_task(realtime.publish(
                            org_id=org_id,
                            topic="errors",
                            event_name="ingestion.error",
                            data={"error": str(parse_exc), "product_id": p.get("id") or p.get("sku")},
                            severity="error",
                            source_id=source_id,
                            request_id="webhook"
                        ))
                    except:
                        pass

            await session.commit()
            
        logger.info("Successfully processed webhook and wrote to outbox.")
        
        # Publish batch progress
        try:
            from app.services.realtime import get_realtime_service
            realtime = get_realtime_service()
            import asyncio
            asyncio.create_task(realtime.publish(
                org_id=org_id,
                topic="ingestion",
                event_name="ingestion.batch_progress",
                data={
                    "received": len(products) + len(deleted_ids),
                    "indexed": indexed_count,
                    "deleted": deleted_count,
                    "failed": failed_count
                },
                severity="info",
                source_id=source_id,
                request_id="webhook"
            ))
        except:
            pass
        
    except Exception as e:
        logger.error(f"Failed to process webhook: {e}")

