"""
Product Service - Layer 5: Domain
Pure business logic, no FastAPI, no LLM imports
Updated to match actual database schema
"""
from typing import Any, Dict, List, Optional

from app.infrastructure.cache.redis import RedisClient
from app.infrastructure.db.firestore import FirestoreClient


class ProductService:
    """Product business logic using actual database schema"""
    
    def __init__(self, firestore: FirestoreClient, cache: RedisClient):
        self.db = firestore
        self.cache = cache
    
    async def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product by ID with caching"""
        cached = await self.cache.get_json(f"product:{product_id}")
        if cached:
            return cached
        
        product = await self.db.get_document('products', product_id)
        if product:
            await self.cache.set_json(f"product:{product_id}", product, ttl=3600)
        
        return product
    
    async def search_products(self, filters: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Search products with filters"""
        return await self.db.query_collection('products', filters, limit)
    
    async def get_trending_products(self, category: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get trending products using actual schema fields"""
        filters = {}
        if category:
            filters['category'] = category
        
        products = await self.db.query_collection('products', filters, limit * 2)
        
        # Sort by rating and discount (using actual schema fields)
        trending_products = []
        for product in products:
            rating = product.get("rating", 0)
            discount = product.get("price", {}).get("discount_percent", 0)
            
            # Simple trending score using available fields
            trending_score = (rating * 0.6) + (discount * 0.004)  # Normalize discount to 0-0.4 range
            
            if trending_score > 0:
                product["trending_score"] = trending_score
                trending_products.append(product)
        
        # Sort by trending score
        trending_products.sort(key=lambda x: x.get("trending_score", 0), reverse=True)
        return trending_products[:limit]
    
    async def get_product_variants(self, product_id: str) -> List[Dict[str, Any]]:
        """Get product variants using actual schema (same brand, different size/color)"""
        product = await self.get_product(product_id)
        if not product:
            return []
        
        brand = product.get("brand")
        category = product.get("category")
        
        if not brand or not category:
            return []
        
        # Find products with same brand and category but different tags
        filters = {
            "brand": brand,
            "category": category
        }
        
        similar_products = await self.db.query_collection('products', filters, 20)
        
        # Filter out the original product and return variants
        variants = [p for p in similar_products if p.get("id") != product_id or p.get("pid") != product_id]
        return variants[:10]
    
    async def get_deals(self, min_discount: float = 20.0, category: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get deals using actual price schema"""
        filters = {}
        if category:
            filters['category'] = category
        
        products = await self.db.query_collection('products', filters, limit * 2)
        
        deals = []
        for product in products:
            price_info = product.get("price", {})
            discount_pct = price_info.get("discount_percent", 0)
            
            if discount_pct >= min_discount:
                # Add deal information using actual schema
                product["deal_discount"] = discount_pct
                product["original_price"] = price_info.get("actual", 0)
                product["sale_price"] = price_info.get("selling", 0)
                product["savings"] = price_info.get("actual", 0) - price_info.get("selling", 0)
                deals.append(product)
        
        # Sort by discount percentage
        deals.sort(key=lambda x: x.get("deal_discount", 0), reverse=True)
        return deals[:limit]
    
    async def check_availability(self, product_id: str) -> Dict[str, Any]:
        """Check product availability using actual availability schema"""
        product = await self.get_product(product_id)
        if not product:
            return {"available": False, "total_stock": 0, "stores": []}
        
        availability = product.get("availability", [])
        total_stock = sum(store.get("quantity", 0) for store in availability)
        
        # Format availability info
        store_info = []
        for store in availability:
            store_info.append({
                "store_id": store.get("store_id"),
                "quantity": store.get("quantity", 0),
                "aisle": store.get("aisle"),
                "shelf": store.get("shelf"),
                "is_backstock": store.get("is_backstock", False)
            })
        
        return {
            "available": total_stock > 0,
            "total_stock": total_stock,
            "online_available": product.get("online_available", False),
            "stock_status": product.get("stock", False),
            "stores": store_info
        }
