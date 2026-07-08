"""
Search Suggestions Service - Layer 4: Domain
Handles search autocomplete and trending searches
"""
from typing import Any, Dict, List, Optional

import structlog

from app.infrastructure.cache import CacheClient
from app.infrastructure.search.typesense import TypesenseClient

logger = structlog.get_logger(__name__)


class SearchSuggestionsService:
    """Service for search suggestions and autocomplete"""
    
    def __init__(self, cache: CacheClient, typesense: TypesenseClient):
        self.cache = cache
        self.typesense = typesense
        self.suggestion_cache_ttl = 3600  # 1 hour
        self.trending_cache_ttl = 1800  # 30 minutes
    
    async def get_suggestions(self, query: str, limit: int = 10, collection: str = "products") -> List[str]:
        """Get search suggestions for autocomplete"""
        try:
            if not query or len(query) < 2:
                return []
            
            # Check cache first
            cache_key = f"suggestions:{collection}:{query.lower()}"
            if self.cache:
                cached = await self.cache.get_json(cache_key)
                if cached:
                    return cached[:limit]
            
            # Get suggestions from Typesense
            if not self.typesense:
                return []
            suggestions = await self.typesense.get_suggestions(query, limit, collection=collection)
            
            # Cache results
            if suggestions and self.cache:
                await self.cache.set_json(cache_key, suggestions, self.suggestion_cache_ttl)
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error("get_suggestions_error", query=query, error=str(e))
            return []
    
    async def get_trending_searches(
        self, 
        tenant_id: str = "default",
        limit: int = 10, 
        category: Optional[str] = None,
        days: int = 7,
        collection: str = "products"
    ) -> List[Dict[str, Any]]:
        """Get trending search queries from telemetry"""
        try:
            # 1. Real Telemetry from Redis
            telemetry_key = f"telemetry:{tenant_id}:trending_searches:{days}d"
            if category:
                telemetry_key += f":{category}"
                
            if self.cache:
                # Real telemetry is a sorted set (zset)
                cached = await self.cache.zrevrange(telemetry_key, 0, limit - 1, withscores=True)
                if cached:
                    return [{"query": item[0], "score": item[1]} for item in cached]
            
            # 2. Cold-Start Fallback (no telemetry exists yet)
            fallback_key = f"fallback_trending_searches:{tenant_id}:{category or 'all'}:{days}"
            if self.cache:
                cached_fallback = await self.cache.get_json(fallback_key)
                if cached_fallback:
                    return cached_fallback[:limit]
            
            # For fallback, just return an empty list or basic generic searches
            # Since we can't reliably mock this without searching the DB
            fallback = [{"query": "shoes", "score": 0.5}, {"query": "shirt", "score": 0.4}]
            
            if self.cache:
                await self.cache.set_json(fallback_key, fallback, self.trending_cache_ttl)
            
            return fallback[:limit]
            
        except Exception as e:
            logger.error("get_trending_searches_error", category=category, error=str(e))
            return []
    
    async def get_popular_searches(
        self, 
        tenant_id: str = "default",
        limit: int = 10, 
        collection: str = "products"
    ) -> List[str]:
        """Get most popular searches from telemetry"""
        try:
            telemetry_key = f"telemetry:{tenant_id}:popular_searches"
            if self.cache:
                cached = await self.cache.get_json(telemetry_key)
                if cached:
                    return cached[:limit]
            
            fallback_key = f"fallback_popular_searches:{tenant_id}"
            if self.cache:
                cached_fallback = await self.cache.get_json(fallback_key)
                if cached_fallback:
                    return cached_fallback[:limit]
            
            fallback = ["shoes", "shirt", "pants", "dress"]
            
            if self.cache:
                await self.cache.set_json(fallback_key, fallback, self.trending_cache_ttl)
            
            return fallback[:limit]
            
        except Exception as e:
            logger.error("get_popular_searches_error", error=str(e))
            return []
    
    async def get_category_suggestions(
        self, 
        query: str, 
        limit: int = 5,
        collection: str = "products"
    ) -> List[Dict[str, str]]:
        """Get category suggestions based on query"""
        try:
            cache_key = f"category_suggestions:{collection}:{query.lower()}"
            if self.cache:
                cached = await self.cache.get_json(cache_key)
                if cached:
                    return cached[:limit]
            
            # Get category suggestions
            if not self.typesense:
                return []
            suggestions = await self.typesense.get_category_suggestions(query, limit, collection=collection)
            
            if suggestions and self.cache:
                await self.cache.set_json(cache_key, suggestions, self.suggestion_cache_ttl)
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error("get_category_suggestions_error", query=query, error=str(e))
            return []
    
    async def get_brand_suggestions(
        self, 
        query: str, 
        limit: int = 5,
        collection: str = "products"
    ) -> List[Dict[str, str]]:
        """Get brand suggestions based on query"""
        try:
            cache_key = f"brand_suggestions:{collection}:{query.lower()}"
            if self.cache:
                cached = await self.cache.get_json(cache_key)
                if cached:
                    return cached[:limit]
            
            # Get brand suggestions
            suggestions = await self.typesense.get_brand_suggestions(query, limit, collection=collection)
            
            if suggestions and self.cache:
                await self.cache.set_json(cache_key, suggestions, self.suggestion_cache_ttl)
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error("get_brand_suggestions_error", query=query, error=str(e))
            return []
