import base64
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Optional

from PIL import Image

from app.addons.image.provider import VisionProvider
from app.utils.logger import get_logger

logger = get_logger("vision_local")

class LocalVisionProvider(VisionProvider):
    """
    Offline, CPU-only vision fallback.
    Uses pyzbar for barcodes. Uses mock/fallback for product features.
    """
    def __init__(self):
        self.pyzbar_available = False

    async def initialize(self) -> None:
        try:
            from pyzbar.pyzbar import decode
            self.pyzbar_available = True
            logger.info("Local vision provider initialized (pyzbar available)")
        except ImportError:
            self.pyzbar_available = False
            logger.info("Local vision provider initialized (pyzbar NOT available, pip install pyzbar)")

    def _prepare_image(self, image_data: str) -> Image.Image:
        if image_data.startswith('data:image/'):
            image_data = image_data.split(',', 1)[1]
        image_bytes = base64.b64decode(image_data)
        return Image.open(BytesIO(image_bytes))

    async def detect_barcode(self, image_data: str) -> Dict[str, Any]:
        if not self.pyzbar_available:
            return {
                "success": True,
                "is_barcode": False,
                "barcode_data": None,
                "barcode_type": None,
                "confidence": 1.0,
                "engine": "local_mock"
            }
        
        try:
            image = self._prepare_image(image_data)
            from pyzbar.pyzbar import decode
            barcodes = decode(image)
            
            if barcodes:
                barcode = barcodes[0]
                barcode_data = barcode.data.decode("utf-8")
                barcode_type = barcode.type
                return {
                    "success": True,
                    "is_barcode": True,
                    "barcode_data": barcode_data,
                    "barcode_type": barcode_type,
                    "confidence": 1.0,
                    "engine": "local_pyzbar"
                }
            
            return {
                "success": True,
                "is_barcode": False,
                "barcode_data": None,
                "barcode_type": None,
                "confidence": 1.0,
                "engine": "local_pyzbar"
            }
        except Exception as e:
            logger.warning(f"Local barcode detection error: {e}")
            return {"success": False, "error": str(e), "is_barcode": False, "barcode_data": None, "barcode_type": None}

    async def analyze_product_features(self, image_data: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Without a local VLM (like Llava), we use a mock for product features
        # In a real SME deployment, this could use a small ONNX model or keyword matching
        return {
            "success": True,
            "category": "General",
            "sub_category": "Item",
            "product_type": "Product",
            "brand": None,
            "attributes": {
                "color": "unknown",
                "pattern": "unknown",
            },
            "confidence": 0.5,
            "description": "Local CPU-only fallback classification.",
            "analysis_timestamp": datetime.now().isoformat()
        }
