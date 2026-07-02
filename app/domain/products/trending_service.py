"""
Trending Products Service - Layer 5: Domain
Handles trending products and deals based on actual database fields
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.infrastructure.cache.redis import RedisClient
from app.infrastructure.db.postgres import PostgresClient
from app.utils.logger import get_logger

logger = get_logger("trending_products")


class TrendingProductsService:
    """Service for trending products and deals using available database fields"""
    
    def __init__(self, cache: RedisClient, db: PostgresClient):
        self.cache = cache
        self.db = db
        self.trending_cache_ttl = 1800  # 30 minutes
        self.deals_cache_ttl = 900  # 15 minutes
    
    async def get_trending_products(
        self,
        tenant_id: str = "default",
        category: Optional[str] = None,
        limit: int = 20,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get trending products based on telemetry (clicks).
        Uses a cold-start fallback if no telemetry is available for the tenant.
        """
        try:
            # 1. Try to get telemetry from Redis
            telemetry_key = f"telemetry:{tenant_id}:trending_products:{days}d"
            if category:
                telemetry_key += f":{category}"
                
            if self.cache:
                cached = await self.cache.get_json(telemetry_key)
                if cached:
                    return {
                        "success": True,
                        "products": cached[:limit],
                        "criteria": "telemetry",
                        "period_days": days,
                        "algorithm": "Click Telemetry",
                        "total_found": len(cached)
                    }

            # 2. Cold-Start Fallback (Catalog data)
            fallback_key = f"fallback_trending:{tenant_id}:{category or 'all'}:{days}"
            if self.cache:
                cached_fallback = await self.cache.get_json(fallback_key)
                if cached_fallback:
                    return {
                        "success": True,
                        "products": cached_fallback[:limit],
                        "criteria": "fallback",
                        "period_days": days,
                        "algorithm": "Basic Catalog Data",
                        "total_found": len(cached_fallback)
                    }

            filters = {}
            if tenant_id != "default":
                filters["tenant_id"] = tenant_id
            if category:
                filters["category"] = category

            products = await self.db.search_products(filters, limit * 2)
            
            # Simple fallback sorting
            for product in products:
                rating = product.get("rating", 0) or 0
                discount = product.get("price", {}).get("discount_percent", 0) or 0
                product["trending_score"] = round((rating * 0.6) + (discount * 0.01), 3)
                
            products.sort(key=lambda x: x.get("trending_score", 0), reverse=True)
            products = products[:limit]

            if products and self.cache:
                await self.cache.set_json(fallback_key, products, self.trending_cache_ttl)

            return {
                "success": True,
                "products": products,
                "criteria": "fallback",
                "period_days": days,
                "algorithm": "Basic Catalog Data",
                "total_found": len(products)
            }
        except Exception as e:
            logger.error(f"get_trending_products_error for category {category}: {e}")
            raise Exception(f"Failed to get trending products: {str(e)}")
    
    async def get_deals(
        self,
        category: Optional[str] = None,
        min_discount: float = 20.0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get products with significant discounts using actual price fields:
        - Uses price.actual (original price) and price.selling (current price)
        - Filters by minimum discount percentage
        - Sorts by discount percentage
        """
        try:
            # Check cache first
            cache_key = f"deals:{category or 'all'}:{min_discount}"
            if self.cache:
                cached = await self.cache.get_json(cache_key)
                if cached:
                    return {
                        "success": True,
                        "deals": cached[:limit],
                        "average_discount": self._calculate_avg_discount(cached),
                        "algorithm": "((actual_price - selling_price) / actual_price) × 100"
                    }
            
            # Query deals from Postgres
            filters = {}
            if category:
                filters['category'] = category
            
            # Get all products and filter by discount
            products = await self.db.search_products(filters, limit * 3)
            
            deals = []
            for product in products:
                # Check if product has price information
                price_info = product.get("price", {})
                actual_price = price_info.get("actual")
                selling_price = price_info.get("selling")
                
                if actual_price and selling_price and actual_price > selling_price:
                    # Calculate discount percentage
                    discount_pct = ((actual_price - selling_price) / actual_price) * 100
                    
                    if discount_pct >= min_discount:
                        # Use existing discount_percent if available, otherwise calculate
                        stored_discount = price_info.get("discount_percent")
                        if stored_discount:
                            product["discount_percentage"] = round(stored_discount, 2)
                        else:
                            product["discount_percentage"] = round(discount_pct, 2)
                        
                        product["savings_amount"] = round(actual_price - selling_price, 2)
                        deals.append(product)
            
            # Sort by discount percentage
            deals.sort(key=lambda x: x.get("discount_percentage", 0), reverse=True)
            deals = deals[:limit]
            
            # Cache results
            if deals and self.cache:
                await self.cache.set_json(cache_key, deals, self.deals_cache_ttl)
            
            return {
                "success": True,
                "deals": deals,
                "average_discount": self._calculate_avg_discount(deals),
                "algorithm": "((actual_price - selling_price) / actual_price) × 100",
                "total_found": len(deals)
            }
            
        except Exception as e:
            logger.error(f"get_deals_error for category {category}: {e}")
            raise Exception(f"Failed to get deals: {str(e)}")
    
    async def get_flash_deals(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get flash deals - products with high discounts (since stock levels are generally high)
        Updated criteria: High discount (>40%) regardless of stock, sorted by urgency
        """
        try:
            cache_key = "flash_deals"
            if self.cache:
                cached = await self.cache.get_json(cache_key)
                if cached:
                    return {
                        "success": True,
                        "deals": cached[:limit],
                        "expires_soon": True,
                        "algorithm": "High discount (>40%) + Urgency scoring"
                    }
            
            # Get products with high discounts
            products = await self.db.search_products({}, limit * 3)
            
            flash_deals = []
            for product in products:
                price_info = product.get("price", {})
                discount_pct = price_info.get("discount_percent", 0)
                
                # Flash deal criteria: high discount (>40%)
                if discount_pct > 40:
                    # Calculate total stock for urgency scoring
                    availability = product.get("availability", [])
                    total_stock = sum(store.get("quantity", 0) for store in availability)
                    
                    # Urgency score: higher discount + lower stock relative to discount
                    # This creates urgency even with higher stock levels
                    stock_factor = max(0.1, min(1.0, 100 / max(total_stock, 1)))  # Inverse stock factor
                    urgency_score = (discount_pct / 100) * (0.7 + 0.3 * stock_factor)
                    
                    product["flash_deal_discount"] = discount_pct
                    product["flash_deal_stock"] = total_stock
                    product["urgency_score"] = round(urgency_score, 3)
                    product["savings_amount"] = round(
                        price_info.get("actual", 0) - price_info.get("selling", 0), 2
                    )
                    flash_deals.append(product)
            
            # Sort by urgency score (high discount with stock consideration)
            flash_deals.sort(key=lambda x: x.get("urgency_score", 0), reverse=True)
            flash_deals = flash_deals[:limit]
            
            # Cache with short TTL
            if flash_deals and self.cache:
                await self.cache.set_json(cache_key, flash_deals, 300)  # 5 minutes
            
            return {
                "success": True,
                "deals": flash_deals,
                "expires_soon": True,
                "algorithm": "High discount (>40%) + Urgency scoring",
                "total_found": len(flash_deals)
            }
            
        except Exception as e:
            logger.error(f"get_flash_deals_error: {e}")
            raise Exception(f"Failed to get flash deals: {str(e)}")
    
    def _calculate_avg_discount(self, products: List[Dict[str, Any]]) -> float:
        """Calculate average discount percentage"""
        if not products:
            return 0.0
        
        total_discount = sum(p.get("discount_percentage", 0) for p in products)
        return round(total_discount / len(products), 2)
