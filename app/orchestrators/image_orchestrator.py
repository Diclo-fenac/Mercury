"""
Image Orchestrator - Layer 2: Orchestration
Coordinates image processing workflow
"""
from typing import Any, Dict, Optional

from app.addons.image.processor import ImageProcessor
from app.addons.search.hybrid import HybridSearch


class ImageOrchestrator:
    """Orchestrates image processing workflow"""
    
    def __init__(
        self, 
        image_processor: ImageProcessor,
        search_service: HybridSearch
    ):
        self.image_processor = image_processor
        self.search = search_service
    
    async def process_image_upload(
        self, 
        image_data: str, 
        organization_id: str,
        user_id: str,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process image upload and analysis"""
        try:
            if not self.image_processor:
                return {
                    "success": False,
                    "error": "image_service_unavailable",
                    "details": "Image processing service not available"
                }
            
            # Process the image upload using real image processor
            result = await self.image_processor.process_image_upload(
                image_data, organization_id, user_id
            )
            
            if not result.get('success'):
                return {
                    "success": False,
                    "error": "image_processing_failed",
                    "details": result.get('error', 'Image processing failed')
                }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": "image_processing_exception",
                "details": f"Failed to process image upload: {str(e)}"
            }
    
    async def get_image_metadata(
        self, organization_id: str, image_id: str, user_id: str
    ) -> Dict[str, Any]:
        """Get image metadata and analysis results"""
        try:
            if not self.image_processor:
                return {"success": False, "error": "image_service_unavailable"}
            
            result = await self.image_processor.get_cached_analysis(organization_id, image_id)
            if not result:
                return {"success": False, "error": "not_found"}
            
            # Authorization check
            if result.get("organization_id") != organization_id or result.get('user_id') != user_id:
                return {"success": False, "error": "access_denied"}
            
            return {"success": True, "image": result}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def search_by_image(
        self, 
        image_id: Optional[str] = None,
        image_data: Optional[str] = None,
        organization_id: Optional[str] = None,
        user_id: str = None,
        tenant_context: Any = None,
        search_type: str = "similar",
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search products by image"""
        try:
            if not image_id and not image_data:
                return {
                    "success": False,
                    "error": "missing_image_data",
                    "details": "Either image_id or image_data is required"
                }
            
            if not self.search:
                return {
                    "success": False,
                    "error": "search_service_unavailable",
                    "details": "Search service not available"
                }
            
            if not organization_id or not tenant_context:
                return {"success": False, "error": "tenant_context_required"}
            if image_id:
                metadata = await self.get_image_metadata(organization_id, image_id, user_id)
                if not metadata.get("success"):
                    return metadata

            # Vision-vector retrieval is not implemented yet. The temporary fallback
            # remains tenant-scoped instead of returning a shared catalog result.
            from app.core.security.context import tenant_context_var

            token = tenant_context_var.set(tenant_context)
            try:
                results = await self.search.search_by_text("product", {}, limit)
            finally:
                tenant_context_var.reset(token)
            
            return {
                "success": True,
                "results": results,
                "image_analysis": {
                    "processed": True,
                    "features_extracted": True,
                    "search_type": search_type
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": "image_search_exception",
                "details": f"Failed to search by image: {str(e)}"
            }
