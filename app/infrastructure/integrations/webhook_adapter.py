"""
Webhook Catalog Integration Adapter
"""
from typing import Any, Dict, List

from app.infrastructure.integrations.base import CatalogIntegrationAdapter


class WebhookIntegrationAdapter(CatalogIntegrationAdapter):
    """Adapter for receiving catalog updates via webhook"""
    
    async def fetch_catalog(self) -> List[Dict[str, Any]]:
        # Webhooks don't "fetch" the whole catalog on demand in the same way,
        # but they might implement a reconciliation sync endpoint if configured.
        return []

    async def validate_config(self) -> bool:
        return bool(self.config.get("webhook_secret"))
