"""
Product Orchestrator - Layer 2: Orchestration
Coordinates product workflow
"""
from typing import Dict, Any, List, Optional
from app.domain.products.service import ProductService
from app.domain.users.service import UserService


class ProductOrchestrator:
    """Orchestrates product workflow"""
    
    def __init__(self, product_service: ProductService, user_service: UserService, trending_service):
        self.products = product_service
        self.users = user_service
        self.trending = trending_service
    
    async def get_trending_products(self, category: Optional[str] = None, limit: int = 20, days: int = 7) -> Dict[str, Any]:
        """Get trending products"""
        try:
            result = await self.trending.get_trending_products(category, limit, days)
            return result
        except Exception as e:
            raise Exception(f"Failed to get trending products: {str(e)}")
    
    async def get_deals(self, category: Optional[str] = None, min_discount: float = 20.0, limit: int = 20) -> Dict[str, Any]:
        """Get product deals"""
        try:
            result = await self.trending.get_deals(category, min_discount, limit)
            return result
        except Exception as e:
            raise Exception(f"Failed to get deals: {str(e)}")
    
    async def get_flash_deals(self, limit: int = 10) -> Dict[str, Any]:
        """Get flash deals"""
        try:
            result = await self.trending.get_flash_deals(limit)
            return result
        except Exception as e:
            raise Exception(f"Failed to get flash deals: {str(e)}")
    
    async def get_product_details(self, product_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed product information"""
        try:
            product = await self.products.get_product(product_id)
            
            if not product:
                return {"success": False, "error": "not_found"}
            
            # Log user activity if user_id provided
            if user_id:
                await self.users.log_activity(user_id, 'product_view', {'product_id': product_id})
            
            return {
                "success": True,
                "product": product
            }
        except Exception as e:
            raise Exception(f"Failed to get product details: {str(e)}")