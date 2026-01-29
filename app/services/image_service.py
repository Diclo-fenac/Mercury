"""
Image Service
Image upload, processing, and analysis
"""
import base64
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from app.services.container import ServiceInterface
from app.core.logging import get_logger

logger = get_logger("image")

class ImageService(ServiceInterface):
    """Async image service for image operations"""
    
    def __init__(
        self,
        bucket_name: str = "walmart-sparkathon-images",
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        allowed_types: list = None
    ):
        self.bucket_name = bucket_name
        self.max_file_size = max_file_size
        self.allowed_types = allowed_types or ["image/jpeg", "image/png", "image/gif", "image/webp"]
        self.llm_service = None
        self.redis_service = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize image service"""
        self._initialized = True
        logger.info("✅ Image service initialized")
    
    async def cleanup(self) -> None:
        """Cleanup image service"""
        self._initialized = False
        logger.info("✅ Image service cleaned up")
    
    async def health_check(self) -> bool:
        """Check image service health"""
        return self._initialized
    
    def set_dependencies(self, llm_service, redis_service):
        """Set service dependencies"""
        self.llm_service = llm_service
        self.redis_service = redis_service
    
    def _validate_image(self, image_data: str) -> Dict[str, Any]:
        """Validate image data"""
        try:
            if not image_data or not image_data.startswith('data:image/'):
                return {
                    "valid": False,
                    "error": "Invalid image format. Must be base64 encoded with data URL prefix."
                }
            
            # Extract content type and data
            header, data = image_data.split(',', 1)
            content_type = header.split(';')[0].split(':')[1]
            
            if content_type not in self.allowed_types:
                return {
                    "valid": False,
                    "error": f"Unsupported image type: {content_type}"
                }
            
            # Decode and check size
            try:
                image_bytes = base64.b64decode(data)
                if len(image_bytes) > self.max_file_size:
                    return {
                        "valid": False,
                        "error": f"Image too large. Maximum size: {self.max_file_size} bytes"
                    }
            except Exception as e:
                return {
                    "valid": False,
                    "error": f"Invalid base64 data: {str(e)}"
                }
            
            return {
                "valid": True,
                "content_type": content_type,
                "size": len(image_bytes)
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"Image validation error: {str(e)}"
            }
    
    async def process_image_upload(
        self,
        image_data: str,
        user_id: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process image upload"""
        try:
            # Validate image
            validation = self._validate_image(image_data)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": validation["error"]
                }
            
            # Generate image ID
            image_id = f"img_{uuid.uuid4().hex[:12]}_{int(datetime.now().timestamp())}"
            
            # For now, create a placeholder URL
            # In production, this would upload to Google Cloud Storage
            image_url = f"https://storage.googleapis.com/{self.bucket_name}/{image_id}.jpg"
            
            # Cache image data for analysis
            if self.redis_service:
                await self.redis_service.set_json(
                    f"image_data:{image_id}",
                    {
                        "image_data": image_data,
                        "user_id": user_id,
                        "filename": filename,
                        "uploaded_at": datetime.now().isoformat(),
                        "content_type": validation["content_type"],
                        "size": validation["size"]
                    },
                    ttl=86400  # 24 hours
                )
            
            return {
                "success": True,
                "image_id": image_id,
                "image_url": image_url,
                "content_type": validation["content_type"],
                "size": validation["size"]
            }
            
        except Exception as e:
            logger.error(f"Image upload error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_image(self, image_data: str) -> Dict[str, Any]:
        """Analyze image with AI"""
        try:
            if not self.llm_service:
                return {
                    "success": False,
                    "error": "LLM service not available"
                }
            
            # Use LLM service for image analysis
            result = await self.llm_service.analyze_image(image_data)
            
            if result.get("success"):
                # Extract real analysis data from LLM result
                description = result.get("description", "")
                
                # Calculate confidence based on description length and content
                confidence = 0.95 if len(description) > 50 else 0.8
                confidence = min(confidence, 0.99) if any(word in description.lower() for word in ['product', 'item', 'brand']) else confidence * 0.9
                
                analysis = {
                    "description": description,
                    "is_barcode": self._detect_barcode_patterns(description),
                    "confidence_score": round(confidence, 2),
                    "analysis_type": "ai_vision"
                }
                
                return {
                    "success": True,
                    "analysis": analysis
                }
            else:
                return result
            
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_cached_analysis(self, image_id: str) -> Dict[str, Any]:
        """Get cached image analysis"""
        try:
            if not self.redis_service:
                return {
                    "success": False,
                    "error": "Cache service not available"
                }
            
            # Get cached analysis
            analysis = await self.redis_service.get_json(f"image_analysis:{image_id}")
            
            if analysis:
                return {
                    "success": True,
                    "analysis": analysis,
                    "cached_at": analysis.get("timestamp"),
                    "expires_at": analysis.get("timestamp", 0) + 3600  # Cache expires in 1 hour
                }
            else:
                return {
                    "success": False,
                    "error": "Analysis not found in cache"
                }
            
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            return {
                "success": False,
                "error": str(e)
            }  
  def _detect_barcode_patterns(self, description: str) -> bool:
        """Detect if description mentions barcode-like patterns"""
        barcode_indicators = ['barcode', 'qr code', 'upc', 'ean', 'code', 'scan', 'digits', 'numbers']
        return any(indicator in description.lower() for indicator in barcode_indicators)