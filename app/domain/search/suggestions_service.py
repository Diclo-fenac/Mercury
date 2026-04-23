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
    
    async def get_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get search suggestions for autocomplete"""
        try:
            if not query or len(query) < 2:
                return []
            
            # Check cache first
            cache_key = f"suggestions:{query.lower()}"
            cached = await self.cache.get_json(cache_key)
            if cached:
                return cached[:limit]
            
            # Get suggestions from Typesense
            suggestions = await self.typesense.get_suggestions(query, limit)
            
            # Cache results
            if suggestions:
                await self.cache.set_json(cache_key, suggestions, self.suggestion_cache_ttl)
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error("get_suggestions_error", query=query, error=str(e))
            return []
    
    async def get_trending_searches(
        self, 
        limit: int = 10, 
        category: Optional[str] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get trending search queries"""
        try:
            # Check cache first
            cache_key = f"trending_searches:{category or 'all'}:{days}"
            cached = await self.cache.get_json(cache_key)
            if cached:
                return cached[:limit]
            
            # Get trending from Typesense
            trending = await self.typesense.get_trending_searches(
                limit=limit,
                category=category,
                days=days
            )
            
            # Cache results
            if trending:
                await self.cache.set_json(cache_key, trending, self.trending_cache_ttl)
            
            return trending[:limit]
            
        except Exception as e:
            logger.error("get_trending_searches_error", category=category, error=str(e))
            return []
    
    async def get_popular_searches(self, limit: int = 10) -> List[str]:
        """Get most popular searches"""
        try:
            cache_key = "popular_searches"
            cached = await self.cache.get_json(cache_key)
            if cached:
                return cached[:limit]
            
            # Get popular searches from Typesense
            popular = await self.typesense.get_popular_searches(limit)
            
            if popular:
                await self.cache.set_json(cache_key, popular, self.trending_cache_ttl)
            
            return popular[:limit]
            
        except Exception as e:
            logger.error("get_popular_searches_error", error=str(e))
            return []
    
    async def get_category_suggestions(
        self, 
        query: str, 
        limit: int = 5
    ) -> List[Dict[str, str]]:
        """Get category suggestions based on query"""
        try:
            cache_key = f"category_suggestions:{query.lower()}"
            cached = await self.cache.get_json(cache_key)
            if cached:
                return cached[:limit]
            
            # Get category suggestions
            suggestions = await self.typesense.get_category_suggestions(query, limit)
            
            if suggestions:
                await self.cache.set_json(cache_key, suggestions, self.suggestion_cache_ttl)
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error("get_category_suggestions_error", query=query, error=str(e))
            return []
    
    async def get_brand_suggestions(
        self, 
        query: str, 
        limit: int = 5
    ) -> List[Dict[str, str]]:
        """Get brand suggestions based on query"""
        try:
            cache_key = f"brand_suggestions:{query.lower()}"
            cached = await self.cache.get_json(cache_key)
            if cached:
                return cached[:limit]
            
            # Get brand suggestions
            suggestions = await self.typesense.get_brand_suggestions(query, limit)
            
            if suggestions:
                await self.cache.set_json(cache_key, suggestions, self.suggestion_cache_ttl)
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error("get_brand_suggestions_error", query=query, error=str(e))
            return []
