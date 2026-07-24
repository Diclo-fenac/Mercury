"""
CSV Catalog Integration Adapter
"""
import csv
import io
from typing import Any, Dict, List

import aiohttp

from app.infrastructure.integrations.base import CatalogIntegrationAdapter


class CSVIntegrationAdapter(CatalogIntegrationAdapter):
    """Adapter for importing catalog from a remote CSV file or local file"""
    
    async def fetch_catalog(self) -> List[Dict[str, Any]]:
        csv_url = self.config.get("csv_url")
        if not csv_url:
            return []
            
        async with aiohttp.ClientSession() as session:
            async with session.get(csv_url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch CSV: {response.status}")
                
                content = await response.text()
                f = io.StringIO(content.strip())
                reader = csv.DictReader(f)
                return [row for row in reader]

    async def validate_config(self) -> bool:
        return bool(self.config.get("csv_url"))
