"""
Recommendation Engine - Layer 5: Domain
Pure business logic for recommendations using actual database schema
"""
from typing import List, Dict, Any
from app.domain.products.service import ProductService
from app.domain.users.service import UserService


class RecommendationEngine:
    """Recommendation business logic using actual schema"""
    
    def __init__(self, product_service: ProductService, user_service: UserService):
        self.products = product_service
        self.users = user_service
    
    async def get_similar_products(self, product_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get similar products based on actual schema fields"""
        product = await self.products.get_product(product_id)
        if not product:
            return []
        
        # Use actual schema fields for similarity
        category = product.get('category')
        sub_category = product.get('sub_category')
        brand = product.get('brand')
        
        # Try to find products with same category and sub_category
        filters = {'category': category}
        if sub_category:
            filters['sub_category'] = sub_category
        
        similar = await self.products.search_products(filters, limit * 2)
        
        # Filter out the original product and prioritize same brand
        similar_products = []
        same_brand = []
        
        for p in similar:
            if p.get('id') != product_id and p.get('pid') != product_id:
                if p.get('brand') == brand:
                    same_brand.append(p)
                else:
                    similar_products.append(p)
        
        # Return same brand first, then others
        result = same_brand[:limit] + similar_products[:limit - len(same_brand)]
        return result[:limit]
    
    async def get_complementary_products(self, product_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get complementary products using actual schema"""
        product = await self.products.get_product(product_id)
        if not product:
            return []
        
        category = product.get('category')
        
        # Define complementary categories based on actual data
        complementary_map = {
            'Clothing and Accessories': ['Footwear', 'Bags and Luggage'],
            'Electronics': ['Mobile Accessories', 'Computer Accessories'],
            'Home and Kitchen': ['Home Decor', 'Kitchen Appliances'],
            'Sports and Fitness': ['Fitness Accessories', 'Sports Equipment']
        }
        
        complementary_categories = complementary_map.get(category, [])
        if not complementary_categories:
            # Fallback to different sub_category in same category
            sub_category = product.get('sub_category')
            filters = {'category': category}
            products = await self.products.search_products(filters, limit * 2)
            return [p for p in products if p.get('sub_category') != sub_category][:limit]
        
        # Search in complementary categories
        complementary = []
        for comp_category in complementary_categories:
            filters = {'category': comp_category}
            products = await self.products.search_products(filters, limit)
            complementary.extend(products)
        
        return complementary[:limit]
    
    async def get_substitute_products(self, product_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get substitute products using actual schema"""
        product = await self.products.get_product(product_id)
        if not product:
            return []
        
        category = product.get('category')
        sub_category = product.get('sub_category')
        price_info = product.get('price', {})
        current_price = price_info.get('selling', 0)
        
        # Find products in same category with similar price range
        filters = {'category': category}
        if sub_category:
            filters['sub_category'] = sub_category
        
        candidates = await self.products.search_products(filters, limit * 3)
        
        # Filter substitutes with similar price range (±30%)
        substitutes = []
        price_range_min = current_price * 0.7
        price_range_max = current_price * 1.3
        
        for candidate in candidates:
            if candidate.get('id') == product_id or candidate.get('pid') == product_id:
                continue
            
            candidate_price = candidate.get('price', {}).get('selling', 0)
            if price_range_min <= candidate_price <= price_range_max:
                substitutes.append(candidate)
        
        return substitutes[:limit]
    
    async def get_personalized_recommendations(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recommendations based on user preferences using actual schema"""
        profile = await self.users.get_user_profile(user_id)
        if not profile:
            # Return trending products for new users
            return await self.products.get_trending_products(limit=limit)
        
        preferences = profile.get('preferences', {})
        
        # Use actual preference fields if they exist
        favorite_category = preferences.get('favorite_category')
        preferred_brands = preferences.get('preferred_brands', [])
        budget_range = preferences.get('budget_range', {})
        
        filters = {}
        if favorite_category:
            filters['category'] = favorite_category
        
        products = await self.products.search_products(filters, limit * 2)
        
        # Score products based on preferences
        scored_products = []
        for product in products:
            score = 1.0
            
            # Brand preference
            if preferred_brands and product.get('brand') in preferred_brands:
                score += 0.5
            
            # Budget preference
            if budget_range:
                price = product.get('price', {}).get('selling', 0)
                min_budget = budget_range.get('min', 0)
                max_budget = budget_range.get('max', float('inf'))
                if min_budget <= price <= max_budget:
                    score += 0.3
            
            # Rating boost
            rating = product.get('rating', 0)
            score += rating * 0.1
            
            product['recommendation_score'] = score
            scored_products.append(product)
        
        # Sort by score and return top results
        scored_products.sort(key=lambda x: x.get('recommendation_score', 0), reverse=True)
        return scored_products[:limit]
