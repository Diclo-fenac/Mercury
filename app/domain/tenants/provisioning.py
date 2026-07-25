"""
Tenant Provisioner - Layer 5: Domain
Manages dynamic collection creation and deletion in Typesense for tenant isolation.
"""
from typing import Any, Dict

from app.infrastructure.search.typesense import TypesenseClient
from app.utils.logger import get_logger

logger = get_logger("tenant_provisioner")


class TenantProvisioner:
    """Handles dynamic creation and cleanup of tenant collections in Typesense"""

    def __init__(self, typesense: TypesenseClient):
        self.typesense = typesense

    def build_schema(self, collection_name: str, num_dim: int = 384, image_num_dim: int = 512) -> Dict[str, Any]:
        """Build standard Typesense collection schema for a tenant"""
        return {
            "name": collection_name,
            "fields": [
                {"name": "id", "type": "string"},
                {"name": "name", "type": "string", "optional": True},
                {"name": "title", "type": "string", "optional": True},
                {"name": "brand", "type": "string", "optional": True, "facet": True},
                {"name": "category", "type": "string", "optional": True, "facet": True},
                {"name": "sub_category", "type": "string", "optional": True, "facet": True},
                {"name": "description", "type": "string", "optional": True},
                {"name": "rating", "type": "float"},
                {"name": "stock", "type": "bool", "optional": True},
                {"name": "online_available", "type": "bool", "optional": True},
                {"name": "selling_price", "type": "float", "optional": True},
                # Legacy keyword-only catalogs may not have vectors yet. Hybrid
                # search will still use keyword retrieval while vectors are backfilled.
                {"name": "embedding", "type": "float[]", "num_dim": num_dim, "optional": True},
                {"name": "image_vector", "type": "float[]", "num_dim": image_num_dim, "optional": True},
            ],
            "default_sorting_field": "rating",
        }

    async def provision_tenant(self, org_id: str, num_dim: int = 384) -> bool:
        """Create a dedicated Typesense collection for a tenant"""
        collection_name = f"tenant_{org_id}_products"
        if not self.typesense:
            logger.warning(f"Typesense client missing. Skipping collection provisioning for {collection_name}")
            return True

        if not self.typesense._connected:
            try:
                await self.typesense.connect()
            except Exception as e:
                logger.warning(f"Typesense reconnect attempt failed during provision: {e}")

        if not self.typesense._connected:
            logger.warning(f"Typesense not connected. Skipping collection provisioning for {collection_name}")
            return True

        if await self.typesense.collection_exists(collection_name):
            logger.info(f"Collection {collection_name} already exists for tenant {org_id}")
            return True

        schema = self.build_schema(collection_name, num_dim=num_dim)
        ok = await self.typesense.create_collection(schema)
        if ok:
            logger.info(f"Successfully provisioned collection {collection_name} for tenant {org_id}")
        else:
            logger.warning(f"Failed to provision collection {collection_name} for tenant {org_id}")
        return True

    async def deprovision_tenant(self, org_id: str) -> bool:
        """Delete the dedicated Typesense collection for a tenant"""
        collection_name = f"tenant_{org_id}_products"
        if not self.typesense or not self.typesense._connected:
            logger.error(f"Typesense client not connected. Cannot deprovision {collection_name}")
            return False

        if not await self.typesense.collection_exists(collection_name):
            logger.info(f"Collection {collection_name} does not exist, skipping deprovisioning")
            return True

        ok = await self.typesense.delete_collection(collection_name)
        if ok:
            logger.info(f"Successfully deprovisioned collection {collection_name} for tenant {org_id}")
        else:
            logger.error(f"Failed to deprovision collection {collection_name} for tenant {org_id}")
        return ok
