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
