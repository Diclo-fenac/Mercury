"""
Trending Products Service - Layer 5: Domain
Handles trending products and deals based on actual database fields
"""
from typing import List, Dict, Any, Optional
from app.infrastructure.cache.redis import RedisClient
from app.infrastructure.db.firestore import FirestoreClient
from app.utils.logger import get_logger
from datetime import datetime, timedelta
import random

logger = get_logger("trending_products")


class TrendingProductsService:
    """Service for trending products and deals using available database fields"""
    
    def __init__(self, cache: RedisClient, firestore: FirestoreClient):
        self.cache = cache
        self.firestore = firestore
        self.trending_cache_ttl = 1800  # 30 minutes
        self.deals_cache_ttl = 900  # 15 minutes
    
    async def get_trending_products(
        self,
        category: Optional[str] = None,
        limit: int = 20,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get trending products based on available database fields:
        - Rating (40%): Higher rated products trend more
        - Discount (30%): Products with good discounts trend more  
        - Availability (20%): Products with good stock trend more
        - Recency (10%): Newer products get slight boost
        """
        try:
            # Check cache first
            cache_key = f"trending_products:{category or 'all'}:{days}"
            if self.cache:
                cached = await self.cache.get_json(cache_key)
                if cached:
                    return {
                        "success": True,
                        "products": cached[:limit],
                        "criteria": "rating_discount_availability_recency",
                        "period_days": days,
                        "algorithm": "Rating(40%) + Discount(30%) + Availability(20%) + Recency(10%)"
                    }
            
            # Query products from Firestore
            filters = {}
            if category:
                filters['category'] = category
            
            # Get products and calculate trending scores
            products = await self.firestore.query_collection('products', filters, limit * 3)
            
            # Calculate trending score for each product
            trending_products = []
            current_time = datetime.now()
            
            for product in products:
                # Rating score (0-5 scale, normalize to 0-1)
                rating = product.get("rating", 0)
                rating_score = min(rating / 5.0, 1.0) if rating else 0
                
                # Discount score (0-100% scale, normalize to 0-1)
                discount_percent = product.get("price", {}).get("discount_percent", 0)
                discount_score = min(discount_percent / 100.0, 1.0) if discount_percent else 0
                
                # Availability score (based on total stock across stores)
                availability = product.get("availability", [])
                total_stock = sum(store.get("quantity", 0) for store in availability)
                # Normalize stock (assume 100+ is max score)
                availability_score = min(total_stock / 100.0, 1.0) if total_stock else 0
                
                # Recency score (newer products get boost)
                created_at = product.get("created_at")
                recency_score = 0
                if created_at:
                    try:
                        created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        days_old = (current_time - created_date).days
                        # Products less than 30 days old get recency boost
                        recency_score = max(0, (30 - days_old) / 30.0) if days_old <= 30 else 0
                    except:
                        recency_score = 0
                
                # Weighted trending score
                trending_score = (
                    (rating_score * 0.4) +      # 40% rating
                    (discount_score * 0.3) +    # 30% discount
                    (availability_score * 0.2) + # 20% availability
                    (recency_score * 0.1)       # 10% recency
                )
                
                if trending_score > 0:
                    product["trending_score"] = round(trending_score, 3)
                    product["trending_factors"] = {
                        "rating_score": round(rating_score, 3),
                        "discount_score": round(discount_score, 3),
                        "availability_score": round(availability_score, 3),
                        "recency_score": round(recency_score, 3)
                    }
                    trending_products.append(product)
            
            # Sort by trending score
            trending_products.sort(key=lambda x: x.get("trending_score", 0), reverse=True)
            trending_products = trending_products[:limit]
            
            # Cache results
            if trending_products and self.cache:
                await self.cache.set_json(cache_key, trending_products, self.trending_cache_ttl)
            
            return {
                "success": True,
                "products": trending_products,
                "criteria": "rating_discount_availability_recency",
                "period_days": days,
                "algorithm": "Rating(40%) + Discount(30%) + Availability(20%) + Recency(10%)",
                "total_found": len(trending_products)
            }
            
        except Exception as e:
            logger.error("get_trending_products_error", category=category, error=str(e))
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
            
            # Query deals from Firestore
            filters = {}
            if category:
                filters['category'] = category
            
            # Get all products and filter by discount
            products = await self.firestore.query_collection('products', filters, limit * 3)
            
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
            logger.error("get_deals_error", category=category, error=str(e))
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
            products = await self.firestore.query_collection('products', {}, limit * 3)
            
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
            logger.error("get_flash_deals_error", error=str(e))
            raise Exception(f"Failed to get flash deals: {str(e)}")
    
    def _calculate_avg_discount(self, products: List[Dict[str, Any]]) -> float:
        """Calculate average discount percentage"""
        if not products:
            return 0.0
        
        total_discount = sum(p.get("discount_percentage", 0) for p in products)
        return round(total_discount / len(products), 2)
