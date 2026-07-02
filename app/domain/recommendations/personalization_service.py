"""
Personalization Service - Layer 4: Domain
Handles user personalized recommendations
"""
from typing import Any, Dict, List, Optional

import structlog

from app.infrastructure.cache import CacheClient
from app.infrastructure.db.postgres import PostgresClient

logger = structlog.get_logger(__name__)


class PersonalizationService:
    """Service for personalized product recommendations"""
    
    def __init__(self, cache: CacheClient, db: PostgresClient):
        self.cache = cache
        self.db = db
        self.recommendations_cache_ttl = 3600  # 1 hour
    
    async def get_personalized_recommendations(
        self,
        user_id: str,
        limit: int = 10,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get personalized product recommendations for user"""
        try:
            # Check cache first
            cache_key = f"recommendations:{user_id}:{category or 'all'}"
            if self.cache:
                cached = await self.cache.get_json(cache_key)
                if cached:
                    return {
                        "success": True,
                        "recommendations": cached[:limit],
                        "personalization_type": "cached"
                    }
            
            # Get user profile and activity
            user_profile = await self._get_user_profile(user_id)
            user_activity = await self._get_user_activity(user_id)
            
            if not user_profile:
                # Return trending products for new users
                return await self._get_trending_recommendations(limit, category)
            
            # Build recommendation strategy based on user profile
            recommendations = []
            
            # 1. Collaborative filtering - products liked by similar users
            collab_recs = await self._get_collaborative_recommendations(
                user_id, user_profile, limit // 3
            )
            recommendations.extend(collab_recs)
            
            # 2. Content-based - similar to products user viewed/purchased
            content_recs = await self._get_content_based_recommendations(
                user_profile, user_activity, limit // 3
            )
            recommendations.extend(content_recs)
            
            # 3. Trending in user's preferred categories
            trending_recs = await self._get_trending_in_categories(
                user_profile, limit // 3
            )
            recommendations.extend(trending_recs)
            
            # Deduplicate and limit
            seen_ids = set()
            unique_recs = []
            for rec in recommendations:
                product_id = rec.get("id")
                if product_id not in seen_ids:
                    seen_ids.add(product_id)
                    unique_recs.append(rec)
            
            unique_recs = unique_recs[:limit]
            
            # Filter by category if specified
            if category:
                unique_recs = [r for r in unique_recs if r.get("category") == category]
            
            # Cache results
            if unique_recs and self.cache:
                await self.cache.set_json(cache_key, unique_recs, self.recommendations_cache_ttl)
            
            return {
                "success": True,
                "recommendations": unique_recs,
                "personalization_type": "hybrid",
                "strategies_used": ["collaborative", "content_based", "trending"]
            }
            
        except Exception as e:
            logger.error("get_personalized_recommendations_error", user_id=user_id, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "recommendations": []
            }
    
    async def get_similar_users_recommendations(
        self,
        user_id: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get recommendations from similar users"""
        try:
            # Get user profile
            user_profile = await self._get_user_profile(user_id)
            if not user_profile:
                return {"success": False, "recommendations": []}
            
            # Find similar users
            similar_users = await self._find_similar_users(user_id, user_profile, limit=5)
            
            # Get products liked by similar users
            recommendations = []
            for similar_user_id in similar_users:
                user_activity = await self._get_user_activity(similar_user_id)
                liked_products = user_activity.get("liked_products", [])
                recommendations.extend(liked_products[:limit // len(similar_users)])
            
            # Deduplicate
            seen_ids = set()
            unique_recs = []
            for rec in recommendations:
                product_id = rec.get("id")
                if product_id not in seen_ids:
                    seen_ids.add(product_id)
                    unique_recs.append(rec)
            
            return {
                "success": True,
                "recommendations": unique_recs[:limit],
                "similar_users_count": len(similar_users)
            }
            
        except Exception as e:
            logger.error("get_similar_users_recommendations_error", user_id=user_id, error=str(e))
            return {"success": False, "recommendations": []}
    
    async def get_frequently_bought_together(
        self,
        product_id: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Get products frequently bought together"""
        try:
            cache_key = f"frequently_bought_together:{product_id}"
            if self.cache:
                cached = await self.cache.get_json(cache_key)
                if cached:
                    return {
                        "success": True,
                        "products": cached[:limit]
                    }
            
            # Query co-purchase data
            query = self.db.collection("co_purchases").where(
                "product_id", "==", product_id
            )
            
            products = []
            docs = await query.stream()
            
            for doc in docs:
                data = doc.to_dict()
                co_product_id = data.get("co_product_id")
                frequency = data.get("frequency", 0)
                
                if co_product_id and frequency > 0:
                    # Get product details
                    product_doc = await self.db.collection("products").document(
                        co_product_id
                    ).get()
                    
                    if product_doc.exists:
                        product_data = product_doc.to_dict()
                        product_data["co_purchase_frequency"] = frequency
                        products.append(product_data)
            
            # Sort by frequency
            products.sort(key=lambda x: x.get("co_purchase_frequency", 0), reverse=True)
            products = products[:limit]
            
            if products and self.cache:
                await self.cache.set_json(cache_key, products, self.recommendations_cache_ttl)
            
            return {
                "success": True,
                "products": products
            }
            
        except Exception as e:
            logger.error("get_frequently_bought_together_error", product_id=product_id, error=str(e))
            return {"success": False, "products": []}
    
    async def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile from Postgres"""
        try:
            doc = await self.db.collection("users").document(user_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logger.error("get_user_profile_error", user_id=user_id, error=str(e))
            return None
    
    async def _get_user_activity(self, user_id: str) -> Dict[str, Any]:
        """Get user activity data"""
        try:
            doc = await self.db.collection("user_activity").document(user_id).get()
            if doc.exists:
                return doc.to_dict()
            return {}
        except Exception as e:
            logger.error("get_user_activity_error", user_id=user_id, error=str(e))
            return {}
    
    async def _get_collaborative_recommendations(
        self,
        user_id: str,
        user_profile: Dict[str, Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get collaborative filtering recommendations"""
        try:
            # Find similar users based on preferences
            similar_users = await self._find_similar_users(user_id, user_profile, limit=3)
            
            recommendations = []
            for similar_user_id in similar_users:
                activity = await self._get_user_activity(similar_user_id)
                liked_products = activity.get("liked_products", [])
                recommendations.extend(liked_products[:limit // 3])
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error("get_collaborative_recommendations_error", user_id=user_id, error=str(e))
            return []
    
    async def _get_content_based_recommendations(
        self,
        user_profile: Dict[str, Any],
        user_activity: Dict[str, Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get content-based recommendations"""
        try:
            # Get products user has viewed/purchased
            viewed_products = user_activity.get("viewed_products", [])
            purchased_products = user_activity.get("purchased_products", [])
            
            recommendations = []
            
            # Find similar products
            for product in viewed_products[:5] + purchased_products[:5]:
                product_id = product.get("id")
                if product_id:
                    # Query similar products
                    query = self.db.collection("products").where(
                        "category", "==", product.get("category")
                    )
                    
                    docs = await query.stream()
                    for doc in docs:
                        similar_product = doc.to_dict()
                        if similar_product.get("id") != product_id:
                            recommendations.append(similar_product)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error("get_content_based_recommendations_error", error=str(e))
            return []
    
    async def _get_trending_in_categories(
        self,
        user_profile: Dict[str, Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Get trending products in user's preferred categories"""
        try:
            preferences = user_profile.get("preferences", {})
            favorite_categories = preferences.get("favorite_categories", [])
            
            recommendations = []
            
            for category in favorite_categories[:3]:
                query = self.db.collection("products").where(
                    "category", "==", category
                ).order_by("views", direction="DESCENDING")
                
                docs = await query.stream()
                for doc in docs:
                    product = doc.to_dict()
                    recommendations.append(product)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error("get_trending_in_categories_error", error=str(e))
            return []
    
    async def _find_similar_users(
        self,
        user_id: str,
        user_profile: Dict[str, Any],
        limit: int = 5
    ) -> List[str]:
        """Find users with similar preferences"""
        try:
            preferences = user_profile.get("preferences", {})
            favorite_categories = preferences.get("favorite_categories", [])
            
            similar_users = []
            
            # Find users with overlapping category preferences
            for category in favorite_categories[:3]:
                query = self.db.collection("users").where(
                    "preferences.favorite_categories", "array-contains", category
                )
                
                docs = await query.stream()
                for doc in docs:
                    other_user_id = doc.id
                    if other_user_id != user_id and other_user_id not in similar_users:
                        similar_users.append(other_user_id)
            
            return similar_users[:limit]
            
        except Exception as e:
            logger.error("find_similar_users_error", user_id=user_id, error=str(e))
            return []
    
    async def _get_trending_recommendations(
        self,
        limit: int,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get trending products as fallback"""
        try:
            query = self.db.collection("products")
            
            if category:
                query = query.where("category", "==", category)
            
            query = query.order_by("views", direction="DESCENDING")
            
            products = []
            docs = await query.stream()
            
            for doc in docs:
                products.append(doc.to_dict())
            
            return {
                "success": True,
                "recommendations": products[:limit],
                "personalization_type": "trending"
            }
            
        except Exception as e:
            logger.error("get_trending_recommendations_error", error=str(e))
            return {
                "success": False,
                "recommendations": []
            }
