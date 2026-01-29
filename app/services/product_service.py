"""
Product Service
Product management and search operations
"""
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.container import ServiceInterface
from app.core.logging import get_logger

logger = get_logger("product")

class ProductService(ServiceInterface):
    """Async product service for product operations"""
    
    def __init__(self):
        self.firestore_service = None
        self.search_service = None
        self.redis_service = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize product service"""
        self._initialized = True
        logger.info("✅ Product service initialized")
    
    async def cleanup(self) -> None:
        """Cleanup product service"""
        self._initialized = False
        logger.info("✅ Product service cleaned up")
    
    async def health_check(self) -> bool:
        """Check product service health"""
        return self._initialized
    
    def set_dependencies(self, firestore_service, search_service, redis_service):
        """Set service dependencies"""
        self.firestore_service = firestore_service
        self.search_service = search_service
        self.redis_service = redis_service
    
    async def get_product_by_id(self, product_id: str) -> Dict[str, Any]:
        """Get product by ID with caching"""
        try:
            # Try cache first
            if self.redis_service:
                cached_product = await self.redis_service.get_json(f"product:{product_id}")
                if cached_product:
                    return {
                        "success": True,
                        "product": cached_product,
                        "cached": True
                    }
            
            # Get from Firestore
            if self.firestore_service:
                product = await self.firestore_service.get_product_by_id(product_id)
                if product:
                    # Cache the product
                    if self.redis_service:
                        await self.redis_service.set_json(
                            f"product:{product_id}", 
                            product, 
                            ttl=3600  # 1 hour
                        )
                    
                    return {
                        "success": True,
                        "product": product,
                        "cached": False
                    }
            
            return {
                "success": False,
                "error": "Product not found"
            }
            
        except Exception as e:
            logger.error(f"Error getting product {product_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_products(
        self, 
        query: str, 
        limit: int = 10, 
        rerank: bool = True
    ) -> Dict[str, Any]:
        """Search products using search service"""
        try:
            if not self.search_service:
                return {
                    "success": False,
                    "error": "Search service not available"
                }
            
            # Perform search
            search_result = await self.search_service.search_products(
                query=query,
                limit=limit,
                rerank=rerank
            )
            
            return {
                "success": True,
                "products": search_result.get("products", []),
                "total": search_result.get("total", 0),
                "reranked": rerank,
                "search_metadata": search_result.get("metadata", {})
            }
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_product_by_barcode(self, barcode: str) -> Dict[str, Any]:
        """Get product by barcode"""
        try:
            # Try cache first
            cache_key = f"barcode:{barcode}"
            if self.redis_service:
                cached_result = await self.redis_service.get_json(cache_key)
                if cached_result:
                    return {
                        "success": True,
                        "product": cached_result.get("product"),
                        "barcode_type": cached_result.get("barcode_type"),
                        "cached": True
                    }
            
            # Search in Firestore by barcode
            if self.firestore_service:
                # This would need to be implemented in firestore_service
                # For now, return placeholder
                return {
                    "success": False,
                    "error": "Barcode lookup not implemented yet"
                }
            
            return {
                "success": False,
                "error": "Product not found for barcode"
            }
            
        except Exception as e:
            logger.error(f"Error looking up barcode {barcode}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_product_recommendations(
        self, 
        product_id: str, 
        limit: int = 5,
        recommendation_type: str = "similar"
    ) -> Dict[str, Any]:
        """Get product recommendations"""
        try:
            # Get the original product
            product_result = await self.get_product_by_id(product_id)
            if not product_result.get("success"):
                return product_result
            
            original_product = product_result.get("product")
            
            # Generate recommendations based on type
            if recommendation_type == "similar":
                recommendations = await self._get_similar_products(original_product, limit)
            elif recommendation_type == "complementary":
                recommendations = await self._get_complementary_products(original_product, limit)
            elif recommendation_type == "substitute":
                recommendations = await self._get_substitute_products(original_product, limit)
            elif recommendation_type == "variant":
                recommendations = await self._get_product_variants(original_product, limit)
            else:
                return {
                    "success": False,
                    "error": f"Unknown recommendation type: {recommendation_type}"
                }
            
            return {
                "success": True,
                "recommendations": recommendations,
                "total": len(recommendations),
                "recommendation_type": recommendation_type,
                "criteria": {
                    "based_on": "category and tags",
                    "algorithm": "similarity_matching"
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting recommendations for {product_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_similar_products(self, product: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Get similar products based on category and tags"""
        try:
            if not self.firestore_service:
                return []
            
            # Search by category
            filters = {
                "category": product.get("category"),
                "sub_category": product.get("sub_category")
            }
            
            similar_products = await self.firestore_service.search_products(filters, limit + 1)
            
            # Remove the original product
            similar_products = [
                p for p in similar_products 
                if p.get("id") != product.get("id")
            ]
            
            return similar_products[:limit]
            
        except Exception as e:
            logger.error(f"Error getting similar products: {e}")
            return []
    
    async def _get_complementary_products(self, product: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Get complementary products that go well together"""
        # Placeholder implementation
        return []
    
    async def _get_substitute_products(self, product: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Get substitute products for out-of-stock items"""
        # Placeholder implementation
        return []
    
    async def _get_product_variants(self, product: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """Get product variants (different sizes, colors, etc.)"""
        # Placeholder implementation
        return []
    
    async def get_trending_products(
        self, 
        category: Optional[str] = None,
        limit: int = 20,
        days: int = 7
    ) -> Dict[str, Any]:
        """Get trending products based on user activity"""
        try:
            # Placeholder implementation
            # In a real system, this would analyze user activity data
            
            filters = {}
            if category:
                filters["category"] = category
            
            if self.firestore_service:
                products = await self.firestore_service.search_products(filters, limit)
                
                return {
                    "success": True,
                    "products": products,
                    "total": len(products),
                    "criteria": {
                        "period_days": days,
                        "category": category,
                        "algorithm": "activity_based"
                    }
                }
            
            return {
                "success": False,
                "error": "Firestore service not available"
            }
            
        except Exception as e:
            logger.error(f"Error getting trending products: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_deals(
        self, 
        category: Optional[str] = None,
        min_discount: float = 20.0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get products with significant discounts"""
        try:
            # Placeholder implementation
            # In a real system, this would filter by discount percentage
            
            filters = {}
            if category:
                filters["category"] = category
            
            if self.firestore_service:
                products = await self.firestore_service.search_products(filters, limit)
                
                # Filter by discount (placeholder logic)
                deals = [
                    product for product in products
                    if product.get("price", {}).get("discount_percent", 0) >= min_discount
                ]
                # Calculate real average discount
                total_discount = sum(deal.get('discount_percentage', 0) for deal in deals)
                average_discount = round(total_discount / len(deals), 2) if deals else 0
                
                return {
                    "success": True,
                    "deals": deals,
                    "total": len(deals),
                    "average_discount": average_discount
                }
            
            return {
                "success": False,
                "error": "Firestore service not available"
            }
            
        except Exception as e:
            logger.error(f"Error getting deals: {e}")
            return {
                "success": False,
                "error": str(e)
            }