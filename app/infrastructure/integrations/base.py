"""
Base Catalog Integration Adapter
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional


class CatalogIntegrationAdapter(ABC):
    """Base class for all catalog integration adapters"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    @abstractmethod
    async def fetch_catalog(self) -> List[Dict[str, Any]]:
        """Fetch catalog items from the source"""
        pass
        
    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate the adapter configuration"""
        pass
