"""
Image Processor - Layer 4: Add-ons
Enhanced image upload, processing, barcode detection, and product identification
"""
import base64
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from app.addons.image.provider import VisionProvider
from app.infrastructure.cache.redis import RedisClient
from app.infrastructure.storage.local import LocalStorageClient
from app.utils.logger import get_logger

logger = get_logger("image_processor")

class ImageProcessor:
    """Enhanced image processing with barcode detection and product identification"""
    
    def __init__(self, storage: Optional[LocalStorageClient], cache: Optional[RedisClient], provider: VisionProvider):
        self.storage = storage
        self.cache = cache
        self.provider = provider
    
    def validate_image(self, image_data: str) -> Dict[str, Any]:
        """Validate image data"""
        if not image_data or not image_data.startswith('data:image/'):
            return {"valid": False, "error": "Invalid image format"}
        
        try:
            header, data = image_data.split(',', 1)
            content_type = header.split(';')[0].split(':')[1]
            image_bytes = base64.b64decode(data)
            
            max_size = 10 * 1024 * 1024  # 10MB
            if len(image_bytes) > max_size:
                return {"valid": False, "error": "Image too large"}
            
            return {
                "valid": True,
                "content_type": content_type,
                "size": len(image_bytes),
                "data": data
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    async def upload_image(self, image_data: str, user_id: str) -> Dict[str, Any]:
        """Upload image to storage"""
        validation = self.validate_image(image_data)
        if not validation["valid"]:
            return {"success": False, "error": validation["error"]}
        
        image_id = f"img_{user_id}_{uuid.uuid4().hex[:8]}"
        
        # Upload to local storage
        if self.storage:
            try:
                blob_name = f"{image_id}.jpg"
                success = await self.storage.upload_blob_from_base64(
                    blob_name,
                    validation["data"],
                    validation["content_type"]
                )
                
                if success:
                    image_url = f"/api/v1/images/{image_id}/raw"
                else:
                    image_url = f"/api/v1/images/{image_id}/raw"
            except Exception as e:
                logger.error(f"Error uploading image locally: {e}")
                image_url = f"/api/v1/images/{image_id}/raw"
        else:
            image_url = f"/api/v1/images/{image_id}/raw"
        
        # Cache image data
        if self.cache:
            await self.cache.set_json(
                f"image:{image_id}",
                {
                    "image_id": image_id,
                    "user_id": user_id,
                    "image_url": image_url,
                    "uploaded_at": datetime.now().isoformat()
                },
                ttl=86400
            )
        
        return {
            "success": True,
            "image_id": image_id,
            "image_url": image_url
        }
    
    async def detect_barcode(self, image_data: str) -> Dict[str, Any]:
        """Detect barcode in image using Vision Provider"""
        result = await self.provider.detect_barcode(image_data)
        
        if result.get('is_barcode') and result.get('barcode_data') and self.cache:
            cache_key = f"barcode:{result['barcode_data']}"
            await self.cache.set_json(cache_key, {
                "barcode_data": result['barcode_data'],
                "barcode_type": result['barcode_type'],
                "detected_at": datetime.now().isoformat(),
                "confidence": result.get('confidence', 0.0)
            }, ttl=86400)
            
        return result
    
    async def analyze_product_image(self, image_data: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Multi-step product image analysis workflow:
        1. Barcode detection
        2. Product identification
        3. Search suggestions (exact → similar → category)
        """
        try:
            # Step 1: Barcode detection
            barcode_result = await self.detect_barcode(image_data)
            
            # Step 2: Product identification (even if barcode detected)
            product_analysis = await self._analyze_product_features(image_data, user_context)
            
            # Step 3: Generate search suggestions
            search_suggestions = self._generate_search_suggestions(
                barcode_result, 
                product_analysis,
                user_context
            )
            
            return {
                "success": True,
                "analysis_type": "enhanced",
                "barcode_detection": barcode_result,
                "product_identification": product_analysis,
                "search_suggestions": search_suggestions,
                "workflow_completed": True
            }
            
        except Exception as e:
            logger.error(f"Product image analysis error: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis_type": "failed"
            }
            
    async def _analyze_product_features(self, image_data: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Analyze product features for identification and search"""
        return await self.provider.analyze_product_features(image_data, user_context)
    
    def _generate_search_suggestions(self, barcode_result: Dict, product_analysis: Dict, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate search suggestions based on analysis results"""
        suggestions = {
            "exact_match": [],
            "similar_products": [],
            "category_suggestions": [],
            "search_strategy": "hybrid"
        }
        
        try:
            # Exact match suggestions (barcode-based)
            if barcode_result.get('is_barcode') and barcode_result.get('barcode_data'):
                suggestions["exact_match"].append({
                    "type": "barcode_search",
                    "query": barcode_result['barcode_data'],
                    "barcode_type": barcode_result['barcode_type'],
                    "priority": 1
                })
                suggestions["search_strategy"] = "exact"
            
            # Similar product suggestions (feature-based)
            if product_analysis.get('success'):
                # Brand + product type search
                if product_analysis.get('brand') and product_analysis.get('product_type'):
                    suggestions["similar_products"].append({
                        "type": "brand_product_search",
                        "query": f"{product_analysis['brand']} {product_analysis['product_type']}",
                        "filters": {
                            "brand": product_analysis['brand'],
                            "category": product_analysis.get('category')
                        },
                        "priority": 2
                    })
                
                # Attribute-based search
                attributes = product_analysis.get('attributes', {})
                if attributes.get('color') and product_analysis.get('product_type'):
                    suggestions["similar_products"].append({
                        "type": "attribute_search",
                        "query": f"{attributes['color']} {product_analysis['product_type']}",
                        "filters": {
                            "category": product_analysis.get('category'),
                            "tag_filters": {
                                "Color": attributes['color'],
                                "Type": product_analysis['product_type']
                            }
                        },
                        "priority": 3
                    })
            
            # Category suggestions (fallback)
            if product_analysis.get('category'):
                suggestions["category_suggestions"].append({
                    "type": "category_browse",
                    "category": product_analysis['category'],
                    "sub_category": product_analysis.get('sub_category'),
                    "priority": 4
                })
            
            # Apply user context preferences
            if user_context and user_context.get('preferred_brands'):
                preferred_brands = user_context['preferred_brands']
                for suggestion in suggestions["similar_products"]:
                    if suggestion.get('filters', {}).get('brand') in preferred_brands:
                        suggestion['priority'] -= 1  # Higher priority for preferred brands
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Search suggestion generation error: {e}")
            return suggestions
            
    async def process_image_upload(self, image_data: str, user_id: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Enhanced image upload and analysis workflow
        Combines upload, barcode detection, and product identification
        """
        # Step 1: Upload the image
        upload_result = await self.upload_image(image_data, user_id)
        
        if not upload_result.get('success'):
            return upload_result
        
        # Step 2: Perform enhanced analysis
        analysis_result = await self.analyze_product_image(image_data, user_context)
        
        # Step 3: Cache comprehensive results
        if self.cache and upload_result.get('image_id'):
            cache_data = {
                "image_id": upload_result["image_id"],
                "image_url": upload_result["image_url"],
                "user_id": user_id,
                "analysis": analysis_result,
                "processed_at": datetime.now().isoformat(),
                "user_context": user_context
            }
            
            await self.cache.set_json(
                f"image_analysis:{upload_result['image_id']}",
                cache_data,
                ttl=86400  # 24 hours
            )
        
        return {
            "success": True,
            "image_id": upload_result["image_id"],
            "image_url": upload_result["image_url"],
            "analysis": analysis_result,
            "processing_time": "enhanced",
            "capabilities_used": [
                "barcode_detection",
                "product_identification", 
                "search_suggestions"
            ]
        }
    
    async def get_cached_analysis(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Get cached image analysis results"""
        if self.cache:
            return await self.cache.get_json(f"image_analysis:{image_id}")
        return None