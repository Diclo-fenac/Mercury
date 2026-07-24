"""
Image Intelligence Tools - Layer 3: Intelligence
Function calling tools for image analysis and barcode detection
"""
from typing import Any, Dict, Optional

from app.addons.image.processor import ImageProcessor
from app.utils.logger import get_logger

logger = get_logger("image_tools")


class ImageTools:
    """Image intelligence tools for LLM function calling"""

    def __init__(self, image_processor: ImageProcessor):
        self.image_processor = image_processor

    async def analyze_product_image(
        self,
        image_data: str,
        organization_id: str,
        user_id: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive image analysis workflow
        Multi-step: barcode detection → product identification → search suggestions
        """
        try:
            logger.info(f"🖼️ Starting comprehensive image analysis for user {user_id}")

            # Process image with full analysis
            result = await self.image_processor.process_image_upload(
                image_data,
                organization_id,
                user_id,
                user_context
            )

            if not result.get('success'):
                return {
                    "success": False,
                    "error": result.get('error', 'Image processing failed'),
                    "analysis_type": "failed"
                }

            analysis = result.get('analysis', {})

            # Extract key information for LLM
            response = {
                "success": True,
                "image_id": result.get('image_id'),
                "analysis_type": analysis.get('analysis_type', 'enhanced'),
                "workflow_completed": analysis.get('workflow_completed', False)
            }

            # Add barcode information if detected
            barcode_info = analysis.get('barcode_detection', {})
            if barcode_info.get('is_barcode'):
                response["barcode_detected"] = {
                    "barcode_data": barcode_info.get('barcode_data'),
                    "barcode_type": barcode_info.get('barcode_type'),
                    "confidence": barcode_info.get('confidence', 0.0)
                }

            # Add product identification
            product_info = analysis.get('product_identification', {})
            if product_info.get('success'):
                response["product_identified"] = {
                    "category": product_info.get('category'),
                    "product_type": product_info.get('product_type'),
                    "brand": product_info.get('brand'),
                    "attributes": product_info.get('attributes', {}),
                    "confidence": product_info.get('confidence', 0.0),
                    "description": product_info.get('description', '')
                }

            # Add search suggestions
            search_suggestions = analysis.get('search_suggestions', {})
            if search_suggestions:
                response["search_suggestions"] = {
                    "exact_match": search_suggestions.get('exact_match', []),
                    "similar_products": search_suggestions.get('similar_products', []),
                    "category_suggestions": search_suggestions.get('category_suggestions', []),
                    "recommended_strategy": search_suggestions.get('search_strategy', 'hybrid')
                }

            logger.info(f"✅ Image analysis completed for user {user_id}")
            return response

        except Exception as e:
            logger.error(f"❌ Image analysis error for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis_type": "error"
            }

    async def detect_barcode(self, image_data: str, organization_id: str) -> Dict[str, Any]:
        """
        Focused barcode detection
        MVP: UPC/EAN/QR detection only
        """
        try:
            logger.info("🔍 Starting barcode detection")

            result = await self.image_processor.detect_barcode(image_data, organization_id)

            if not result.get('success'):
                return {
                    "success": False,
                    "error": result.get('error', 'Barcode detection failed'),
                    "is_barcode": False
                }

            response = {
                "success": True,
                "is_barcode": result.get('is_barcode', False),
                "barcode_data": result.get('barcode_data'),
                "barcode_type": result.get('barcode_type'),
                "confidence": result.get('confidence', 0.0)
            }

            if response["is_barcode"]:
                logger.info(f"✅ Barcode detected: {response['barcode_data']} ({response['barcode_type']})")
            else:
                logger.info("ℹ️ No barcode detected in image")

            return response

        except Exception as e:
            logger.error(f"❌ Barcode detection error: {e}")
            return {
                "success": False,
                "error": str(e),
                "is_barcode": False
            }

    async def get_cached_analysis(self, organization_id: str, image_id: str) -> Dict[str, Any]:
        """Get previously cached image analysis"""
        try:
            cached_data = await self.image_processor.get_cached_analysis(organization_id, image_id)

            if cached_data:
                return {
                    "success": True,
                    "cached": True,
                    "image_id": image_id,
                    "analysis": cached_data.get('analysis', {}),
                    "processed_at": cached_data.get('processed_at')
                }
            else:
                return {
                    "success": False,
                    "error": "No cached analysis found",
                    "image_id": image_id
                }

        except Exception as e:
            logger.error(f"❌ Cache retrieval error for image {image_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "image_id": image_id
            }

    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions for LLM registration"""
        return {
            "analyze_product_image": {
                "description": "Comprehensive image analysis: barcode detection + product identification + search suggestions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_data": {
                            "type": "string",
                            "description": "Base64 encoded image data with data URL prefix"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "User identifier for context and caching"
                        },
                        "user_context": {
                            "type": "object",
                            "description": "Optional user preferences and context",
                            "properties": {
                                "preferred_brands": {"type": "array"},
                                "preferred_categories": {"type": "array"},
                                "budget_range": {"type": "object"}
                            }
                        }
                    },
                    "required": ["image_data", "user_id"]
                }
            },
            "detect_barcode": {
                "description": "Focused barcode detection (UPC/EAN/QR codes)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_data": {
                            "type": "string",
                            "description": "Base64 encoded image data with data URL prefix"
                        }
                    },
                    "required": ["image_data"]
                }
            },
            "get_cached_analysis": {
                "description": "Retrieve previously cached image analysis results",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_id": {
                            "type": "string",
                            "description": "Image identifier from previous analysis"
                        }
                    },
                    "required": ["image_id"]
                }
            }
        }
