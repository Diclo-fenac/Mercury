"""
Search Orchestrator - Layer 2: Orchestration
Coordinates search workflow
"""
from typing import Dict, Any, List
from app.addons.search.hybrid import HybridSearch
from app.addons.personalization.scorer import PersonalizationScorer
from app.infrastructure.cache.redis import RedisClient


class SearchOrchestrator:
    """Orchestrates search workflow"""
    
    def __init__(
        self,
        search: HybridSearch,
        personalization: PersonalizationScorer,
        cache: RedisClient
    ):
        self.search = search
        self.personalization = personalization
        self.cache = cache
    
    async def handle(self, query: str, user_id: str, filters: Dict[str, Any] = None, limit: int = 10) -> Dict[str, Any]:
        """Handle search request"""
        try:
            # Search products
            results = await self.search.search(query, filters=filters, limit=limit)
            
            # Personalize results if personalization service available
            if self.personalization:
                try:
                    personalized = await self.personalization.score_products(user_id, results)
                    results = personalized
                except Exception as e:
                    # Log error but continue with unpersonalized results
                    print(f"Personalization error: {e}")
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "total_results": len(results),
                "filters_applied": filters or {}
            }
        except Exception as e:
            raise Exception(f"Search failed: {str(e)}")
    
    async def get_suggestions(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Get search suggestions"""
        try:
            # In a real app, this would use search analytics and user behavior
            # For now, generate contextual suggestions
            suggestions = [
                f"{query} deals",
                f"{query} reviews",
                f"best {query}",
                f"cheap {query}",
                f"{query} sale"
            ][:limit]
            
            return {
                "success": True,
                "suggestions": suggestions
            }
        except Exception as e:
            raise Exception(f"Failed to get suggestions: {str(e)}")
    
    async def get_trending_searches(self, limit: int = 10, category: str = None) -> Dict[str, Any]:
        """Get trending searches"""
        try:
            # In a real app, this would query search analytics
            trending = [
                "wireless headphones",
                "laptop deals",
                "smartphone",
                "gaming chair",
                "coffee maker"
            ][:limit]
            
            return {
                "success": True,
                "searches": trending
            }
        except Exception as e:
            raise Exception(f"Failed to get trending searches: {str(e)}")