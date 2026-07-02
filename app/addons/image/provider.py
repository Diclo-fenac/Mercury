from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class VisionProvider(ABC):
    """Abstract interface for all Vision & Image Analysis providers"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the client/model dependencies"""
        pass

    @abstractmethod
    async def detect_barcode(self, image_data: str) -> Dict[str, Any]:
        """Detect barcode values (UPC, EAN, QR) in base64 image data"""
        pass

    @abstractmethod
    async def analyze_product_features(
        self, 
        image_data: str, 
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Extract product attributes (category, brand, color, type) from base64 image data"""
        pass
