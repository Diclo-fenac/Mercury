"""
Image Processor - Layer 4: Add-ons
Enhanced image upload, processing, barcode detection, and product identification
"""
import base64
import json
import uuid
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Optional

import google.genai as genai
from PIL import Image

from app.infrastructure.cache.redis import RedisClient
from app.infrastructure.storage.gcs import GCSClient
from app.utils.logger import get_logger

logger = get_logger("image_processor")


class ImageProcessor:
    """Enhanced image processing with barcode detection and product identification"""
    
    def __init__(self, storage: Optional[GCSClient], cache: Optional[RedisClient]):
        self.storage = storage
        self.cache = cache
        self.gemini_client = None
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini client for image analysis"""
        try:
            # This will be injected via dependency injection in production
            # For now, we'll initialize it here
            import os
            api_key = os.getenv('GOOGLE_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_client = genai
                logger.info("✅ Gemini client initialized for image analysis")
            else:
                logger.warning("⚠️ Google API key not found, image analysis will be limited")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.gemini_client = None
    
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
        
        # Upload to GCS if available
        if self.storage:
            try:
                blob_name = f"images/{user_id}/{image_id}.jpg"
                success = await self.storage.upload_blob_from_base64(
                    blob_name,
                    validation["data"],
                    validation["content_type"]
                )
                
                if success:
                    image_url = f"https://storage.googleapis.com/{self.storage.bucket_name}/{blob_name}"
                else:
                    image_url = f"local://{image_id}"
            except:
                image_url = f"local://{image_id}"
        else:
            image_url = f"local://{image_id}"
        
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
        """
        Detect barcode in image using Gemini Vision
        Supports UPC, EAN, QR codes (MVP requirement)
        """
        if not self.gemini_client:
            return {
                "success": False,
                "error": "Gemini client not available",
                "is_barcode": False,
                "barcode_data": None,
                "barcode_type": None
            }
        
        try:
            # Prepare image for analysis
            if image_data.startswith('data:image/'):
                image_data = image_data.split(',', 1)[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(BytesIO(image_bytes))
            
            # Specialized barcode detection prompt
            prompt = """
            Analyze this image specifically for BARCODE DETECTION.
            
            Look for:
            - UPC barcodes (vertical black/white lines with numbers below)
            - EAN barcodes (similar to UPC, often 13 digits)
            - QR codes (square black/white patterns)
            
            Return ONLY a JSON response:
            {
                "is_barcode": true/false,
                "barcode_data": "extracted_code_or_null",
                "barcode_type": "UPC|EAN|QR|null",
                "confidence": 0.0-1.0
            }
            
            If no barcode is detected, return:
            {"is_barcode": false, "barcode_data": null, "barcode_type": null, "confidence": 1.0}
            """
            
            # Use Gemini Vision for barcode detection
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content([prompt, image])
            
            # Parse JSON response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            result = json.loads(response_text)
            
            # Cache result if barcode detected
            if result.get('is_barcode') and result.get('barcode_data') and self.cache:
                cache_key = f"barcode:{result['barcode_data']}"
                await self.cache.set_json(cache_key, {
                    "barcode_data": result['barcode_data'],
                    "barcode_type": result['barcode_type'],
                    "detected_at": datetime.now().isoformat(),
                    "confidence": result.get('confidence', 0.0)
                }, ttl=86400)  # Cache for 24 hours
            
            return {
                "success": True,
                "is_barcode": result.get('is_barcode', False),
                "barcode_data": result.get('barcode_data'),
                "barcode_type": result.get('barcode_type'),
                "confidence": result.get('confidence', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Barcode detection error: {e}")
            return {
                "success": False,
                "error": str(e),
                "is_barcode": False,
                "barcode_data": None,
                "barcode_type": None
            }
    
    async def analyze_product_image(self, image_data: str, user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Multi-step product image analysis workflow:
        1. Barcode detection
        2. Product identification
        3. Search suggestions (exact → similar → category)
        """
        if not self.gemini_client:
            return {
                "success": False,
                "error": "Gemini client not available",
                "analysis_type": "basic"
            }
        
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
        try:
            # Prepare image
            if image_data.startswith('data:image/'):
                image_data = image_data.split(',', 1)[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(BytesIO(image_bytes))
            
            # Enhanced product analysis prompt based on schema
            prompt = f"""
            Analyze this product image for e-commerce search optimization.
            
            IDENTIFY:
            1. **Product Category**: Clothing and Accessories, Electronics, Home & Kitchen, etc.
            2. **Product Type**: T-shirt, smartphone, etc.
            3. **Brand**: Any visible brand names or logos
            4. **Key Attributes**:
               - For Clothing: Color, Pattern, Fabric, Fit, Size indicators
               - For Electronics: Brand, model, color, type
               - For FMCG: Brand, flavor, packaging type
            
            USER CONTEXT: {user_context or 'None provided'}
            
            Return JSON:
            {{
                "category": "main_category",
                "sub_category": "specific_type", 
                "product_type": "specific_product",
                "brand": "detected_brand_or_null",
                "attributes": {{
                    "color": "primary_color",
                    "pattern": "pattern_type_or_null",
                    "fabric": "material_type_or_null",
                    "size_indicators": ["visible_size_info"],
                    "other_features": ["additional_attributes"]
                }},
                "confidence": 0.0-1.0,
                "description": "natural_language_description"
            }}
            """
            
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content([prompt, image])
            
            # Parse response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            
            result = json.loads(response_text)
            
            return {
                "success": True,
                "category": result.get('category'),
                "sub_category": result.get('sub_category'),
                "product_type": result.get('product_type'),
                "brand": result.get('brand'),
                "attributes": result.get('attributes', {}),
                "confidence": result.get('confidence', 0.0),
                "description": result.get('description', ''),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Product feature analysis error: {e}")
            return {
                "success": False,
                "error": str(e),
                "confidence": 0.0
            }
    
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