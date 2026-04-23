"""
Search Orchestrator - Layer 2: Orchestration
Coordinates search workflow
"""
from typing import Any, Dict

from app.addons.personalization.scorer import PersonalizationScorer
from app.addons.search.hybrid import HybridSearch
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
    
    async def handle(
        self, 
        query: str, 
        user_id: str, 
        filters: Dict[str, Any] = None, 
        limit: int = 10,
        offset: int = 0,
        sort: Dict[str, Any] = None,
        search_type: str = "hybrid",
        include_suggestions: bool = False
    ) -> Dict[str, Any]:
        """Handle search request with advanced parameters and enhanced response models"""
        import time
        start_time = time.time()
        
        try:
            # Search products
            results = await self.search.search(query, filters=filters, limit=limit)
            
            # Personalize results and add transparency
            personalization_applied = False
            if self.personalization:
                try:
                    personalized = await self.personalization.score_products(user_id, results)
                    results = personalized
                    personalization_applied = True
                except Exception as e:
                    print(f"Personalization error: {e}")
            
            # Process results to add breakdown and metadata
            processed_results = []
            facets = {"brand": {}, "category": {}}
            
            for item in results:
                # Aggregate facets
                brand = item.get('brand', 'Unknown')
                category = item.get('category', 'General')
                facets["brand"][brand] = facets["brand"].get(brand, 0) + 1
                facets["category"][category] = facets["category"].get(category, 0) + 1
                
                # Build score breakdown
                similarity = item.get('similarity_score', 0.0)
                # Map old score if exists
                current_score = item.get('personalization_score') or item.get('variant_score') or similarity or 0.8
                
                breakdown = {
                    "keyword_score": 0.5 if similarity > 0 else 0.8, # Mock logic
                    "semantic_score": similarity,
                    "rrf_score": similarity * 0.9,
                    "personalization_boost": 0.05 if personalization_applied else 0.0
                }
                
                item['score'] = current_score
                item['breakdown'] = breakdown
                processed_results.append(item)
            
            latency = int((time.time() - start_time) * 1000)
            
            return {
                "success": True,
                "query": query,
                "results": processed_results,
                "total_results": len(processed_results),
                "facets": facets,
                "meta": {
                    "latency_ms": latency,
                    "cache_hit": False, # Would come from cache service
                    "search_mode": search_type
                },
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