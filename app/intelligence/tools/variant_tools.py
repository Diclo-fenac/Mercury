"""
Variant Discovery Tools - Layer 3: Intelligence
Function calling tools for product variant and substitute discovery
"""
from typing import Dict, Any, Optional, List
from app.addons.search.hybrid import HybridSearch
from app.utils.logger import get_logger

logger = get_logger("variant_tools")


class VariantTools:
    """Variant and substitute discovery tools for LLM function calling"""
    
    def __init__(self, hybrid_search: HybridSearch):
        self.hybrid_search = hybrid_search
    
    async def find_product_variants(
        self, 
        product_id: str,
        user_id: Optional[str] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
        limit: int = 8
    ) -> Dict[str, Any]:
        """
        Find strict variants of a product (same product, only size/color differences)
        Automatic execution - no user prompt needed per requirements
        """
        try:
            logger.info(f"🔍 Finding variants for product {product_id} (user: {user_id})")
            
            variants = await self.hybrid_search.find_strict_variants(
                product_id, 
                user_preferences,
                limit
            )
            
            if not variants:
                return {
                    "success": True,
                    "product_id": product_id,
                    "variants_found": 0,
                    "variants": [],
                    "message": "No variants found for this product",
                    "execution_type": "automatic"
                }
            
            # Categorize variants by type
            variant_categories = self._categorize_variants(variants)
            
            # Generate user-friendly summary
            summary = self._generate_variant_summary(variants, variant_categories)
            
            logger.info(f"✅ Found {len(variants)} variants for product {product_id}")
            
            return {
                "success": True,
                "product_id": product_id,
                "variants_found": len(variants),
                "variants": variants,
                "variant_categories": variant_categories,
                "summary": summary,
                "execution_type": "automatic",
                "user_message": f"I found {len(variants)} variants of this product in different sizes and colors."
            }
            
        except Exception as e:
            logger.error(f"❌ Error finding variants for product {product_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "product_id": product_id,
                "variants_found": 0
            }
    
    async def suggest_product_substitutes(
        self,
        product_id: str,
        substitute_type: str = "price_focused",  # price_focused, availability_focused, quality_focused
        user_id: Optional[str] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
        limit: int = 6
    ) -> Dict[str, Any]:
        """
        Suggest product substitutes (user-triggered only per requirements)
        This should only be called when user explicitly asks for alternatives
        """
        try:
            logger.info(f"🔄 Finding {substitute_type} substitutes for product {product_id}")
            
            substitutes = await self.hybrid_search.find_substitutes(
                product_id,
                substitute_type,
                user_preferences,
                limit
            )
            
            if not substitutes:
                return {
                    "success": True,
                    "product_id": product_id,
                    "substitute_type": substitute_type,
                    "substitutes_found": 0,
                    "substitutes": [],
                    "message": f"No {substitute_type.replace('_', ' ')} substitutes found",
                    "execution_type": "user_triggered"
                }
            
            # Generate substitute summary
            summary = self._generate_substitute_summary(substitutes, substitute_type)
            
            logger.info(f"✅ Found {len(substitutes)} {substitute_type} substitutes")
            
            return {
                "success": True,
                "product_id": product_id,
                "substitute_type": substitute_type,
                "substitutes_found": len(substitutes),
                "substitutes": substitutes,
                "summary": summary,
                "execution_type": "user_triggered",
                "user_message": f"Here are {len(substitutes)} {substitute_type.replace('_', ' ')} alternatives:"
            }
            
        except Exception as e:
            logger.error(f"❌ Error finding substitutes for product {product_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "product_id": product_id,
                "substitute_type": substitute_type,
                "substitutes_found": 0
            }
    
    async def check_product_availability(
        self,
        product_id: str,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Check product availability and suggest alternatives if out of stock
        Automatic execution when product is unavailable
        """
        try:
            # This would typically check real inventory
            # For now, we'll simulate based on product data
            
            # Get product from Firestore
            product = await self.hybrid_search.db.get_product_by_id(product_id)
            
            if not product:
                return {
                    "success": False,
                    "error": "Product not found",
                    "product_id": product_id
                }
            
            is_available = product.get('stock', False) and product.get('online_available', False)
            
            result = {
                "success": True,
                "product_id": product_id,
                "is_available": is_available,
                "stock_status": "in_stock" if is_available else "out_of_stock",
                "online_available": product.get('online_available', False)
            }
            
            # If out of stock, automatically suggest alternatives
            if not is_available:
                logger.info(f"📦 Product {product_id} is out of stock, finding alternatives")
                
                # Find in-stock variants first
                variants = await self.find_product_variants(product_id, user_preferences=user_preferences)
                in_stock_variants = [
                    v for v in variants.get('variants', []) 
                    if v.get('stock') and v.get('online_available')
                ]
                
                result.update({
                    "alternatives_suggested": True,
                    "in_stock_variants": len(in_stock_variants),
                    "variants": in_stock_variants[:3],  # Show top 3
                    "user_message": f"This item is out of stock. I found {len(in_stock_variants)} similar items available."
                })
                
                # If no variants available, suggest substitutes
                if not in_stock_variants:
                    substitutes = await self.suggest_product_substitutes(
                        product_id, 
                        "availability_focused",
                        user_preferences=user_preferences,
                        limit=3
                    )
                    result.update({
                        "substitutes": substitutes.get('substitutes', []),
                        "user_message": "This item is out of stock. Here are some available alternatives:"
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error checking availability for product {product_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "product_id": product_id
            }
    
    def _categorize_variants(self, variants: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize variants by type (size, color, both)"""
        categories = {
            "size_variants": [],
            "color_variants": [],
            "size_and_color_variants": []
        }
        
        for variant in variants:
            variant_type = variant.get('variant_type', 'identical')
            if variant_type == 'size_variant':
                categories["size_variants"].append(variant)
            elif variant_type == 'color_variant':
                categories["color_variants"].append(variant)
            elif variant_type == 'size_and_color':
                categories["size_and_color_variants"].append(variant)
        
        return categories
    
    def _generate_variant_summary(self, variants: List[Dict[str, Any]], categories: Dict[str, List]) -> Dict[str, Any]:
        """Generate user-friendly variant summary"""
        summary = {
            "total_variants": len(variants),
            "available_sizes": set(),
            "available_colors": set(),
            "in_stock_count": 0,
            "price_range": {"min": float('inf'), "max": 0}
        }
        
        for variant in variants:
            # Collect available sizes and colors
            tags = variant.get('tags', {})
            if tags.get('Size'):
                summary["available_sizes"].add(tags['Size'])
            if tags.get('Color'):
                summary["available_colors"].add(tags['Color'])
            
            # Count in-stock variants
            if variant.get('stock'):
                summary["in_stock_count"] += 1
            
            # Track price range
            price = variant.get('price', {}).get('selling', 0)
            if price > 0:
                summary["price_range"]["min"] = min(summary["price_range"]["min"], price)
                summary["price_range"]["max"] = max(summary["price_range"]["max"], price)
        
        # Convert sets to sorted lists
        summary["available_sizes"] = sorted(list(summary["available_sizes"]))
        summary["available_colors"] = sorted(list(summary["available_colors"]))
        
        # Handle price range edge case
        if summary["price_range"]["min"] == float('inf'):
            summary["price_range"] = {"min": 0, "max": 0}
        
        return summary
    
    def _generate_substitute_summary(self, substitutes: List[Dict[str, Any]], substitute_type: str) -> Dict[str, Any]:
        """Generate user-friendly substitute summary"""
        summary = {
            "total_substitutes": len(substitutes),
            "substitute_type": substitute_type,
            "average_savings": 0,
            "in_stock_count": 0,
            "brands": set()
        }
        
        total_savings = 0
        savings_count = 0
        
        for substitute in substitutes:
            # Count in-stock substitutes
            if substitute.get('stock'):
                summary["in_stock_count"] += 1
            
            # Collect brands
            if substitute.get('brand'):
                summary["brands"].add(substitute['brand'])
            
            # Calculate average savings for price-focused substitutes
            if substitute_type == "price_focused":
                price_comparison = substitute.get('price_comparison', {})
                if price_comparison.get('is_cheaper'):
                    total_savings += price_comparison.get('savings', 0)
                    savings_count += 1
        
        # Calculate average savings
        if savings_count > 0:
            summary["average_savings"] = round(total_savings / savings_count, 2)
        
        summary["brands"] = sorted(list(summary["brands"]))
        
        return summary
    
    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions for LLM registration"""
        return {
            "find_product_variants": {
                "description": "Find strict variants of a product (same product, different size/color only). Executes automatically.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "Product ID to find variants for"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "Optional user ID for personalization"
                        },
                        "user_preferences": {
                            "type": "object",
                            "description": "Optional user preferences for ranking",
                            "properties": {
                                "preferred_colors": {"type": "array"},
                                "preferred_size": {"type": "array"},
                                "budget_range": {"type": "object"}
                            }
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of variants to return",
                            "default": 8
                        }
                    },
                    "required": ["product_id"]
                }
            },
            "suggest_product_substitutes": {
                "description": "Suggest product substitutes (user-triggered only). Only call when user explicitly asks for alternatives.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "Product ID to find substitutes for"
                        },
                        "substitute_type": {
                            "type": "string",
                            "enum": ["price_focused", "availability_focused", "quality_focused"],
                            "description": "Type of substitutes to find",
                            "default": "price_focused"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "Optional user ID for personalization"
                        },
                        "user_preferences": {
                            "type": "object",
                            "description": "Optional user preferences for ranking"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of substitutes to return",
                            "default": 6
                        }
                    },
                    "required": ["product_id"]
                }
            },
            "check_product_availability": {
                "description": "Check product availability and suggest alternatives if out of stock. Executes automatically.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {
                            "type": "string",
                            "description": "Product ID to check availability for"
                        },
                        "user_preferences": {
                            "type": "object",
                            "description": "Optional user preferences for alternative suggestions"
                        }
                    },
                    "required": ["product_id"]
                }
            }
        }