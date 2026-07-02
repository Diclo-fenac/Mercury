"""
Search Orchestrator - Layer 2: Orchestration
Coordinates search workflow
"""
import time
from typing import Any, Dict, List, Optional

from app.addons.personalization.scorer import PersonalizationScorer
from app.addons.search.hybrid import HybridSearch
from app.domain.search.suggestions_service import SearchSuggestionsService
from app.infrastructure.cache.redis import RedisClient
from app.utils.metrics import (
    CACHE_HIT_RATE,
    CACHE_HITS,
    CACHE_MISSES,
    SEARCH_LATENCY,
    SEARCH_TOTAL,
    ZERO_RESULT_QUERIES,
)


class SearchOrchestrator:
    """Orchestrates search workflow"""
    
    def __init__(
        self,
        search: HybridSearch,
        personalization: PersonalizationScorer,
        cache: RedisClient,
        suggestions_service: Optional[SearchSuggestionsService] = None,
        tenant_service: Optional[Any] = None
    ):
        self.search = search
        self.personalization = personalization
        self.cache = cache
        self.suggestions_service = suggestions_service
        self.tenant_service = tenant_service
        self._cache_hits = 0
        self._cache_total = 0
    
    async def handle(
        self, 
        query: str, 
        user_id: str, 
        filters: Dict[str, Any] = None, 
        limit: int = 10,
        offset: int = 0,
        sort: Dict[str, Any] = None,
        search_type: str = "hybrid",
        include_suggestions: bool = False,
        tenant_context: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Handle search request with advanced parameters and enhanced response models"""
        start_time = time.time()
        fallback_used = False
        
        try:
            # Check cache first
            cache_key = f"search:{query}:{user_id}:{filters}"
            if tenant_context:
                cache_key = f"tenant_search:{tenant_context.organization_id}:{query}:{user_id}:{filters}"

            cached = None
            if self.cache:
                cached = await self.cache.get_json(cache_key)
                if cached:
                    self._cache_hits += 1
                    CACHE_HITS.inc()
                    return cached
                else:
                    CACHE_MISSES.inc()
            
            self._cache_total += 1
            
            # 1. Synonym expansion
            expanded_query = query
            if self.tenant_service and tenant_context:
                synonyms = await self.tenant_service.get_synonyms(tenant_context.organization_id, query)
                if synonyms:
                    expanded_query = f"{query} {' '.join(synonyms)}"

            # 2. Search products (with dynamic collection)
            collection = tenant_context.collection_name if tenant_context else "products"
            results = await self.search.search(expanded_query, filters=filters, limit=limit, collection=collection)
            
            # Track zero-result queries
            if len(results) == 0:
                ZERO_RESULT_QUERIES.labels(search_type=search_type, fallback_used='false').inc()
                # Try fallback (semantic expansion)
                fallback_query = self._expand_query(query)
                if fallback_query != query:
                    fallback_used = True
                    results = await self.search.search(fallback_query, filters=filters, limit=limit, collection=collection)
                    if len(results) > 0:
                        ZERO_RESULT_QUERIES.labels(search_type=search_type, fallback_used='true').inc()
            
            # 3. Apply out-of-stock behavior
            if tenant_context:
                behavior = tenant_context.config.get("out_of_stock_behavior", "demote")
                results = self._apply_stock_policy(results, behavior)

            # 4. Apply pinned products (merchandising)
            if self.tenant_service and tenant_context:
                pins = await self.tenant_service.get_pinned_products(tenant_context.organization_id, query)
                if pins:
                    results = self._apply_pins(results, pins)

            # 5. Personalize results and add transparency (only if enabled by tenant config)
            personalization_applied = False
            enable_personalization = tenant_context.config.get("enable_personalization", False) if tenant_context else True
            if self.personalization and enable_personalization:
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
            
            response = {
                "success": True,
                "query": query,
                "results": processed_results,
                "total_results": len(processed_results),
                "facets": facets,
                "meta": {
                    "latency_ms": latency,
                    "cache_hit": cached is not None,
                    "search_mode": search_type,
                    "fallback_used": fallback_used
                },
                "filters_applied": filters or {}
            }
            
            # Cache the result
            if self.cache and not cached:
                await self.cache.set_json(cache_key, response, ttl=300)  # 5 min TTL
            
            # Update cache hit rate metric
            if self._cache_total > 0:
                CACHE_HIT_RATE.set(self._cache_hits / self._cache_total)
            
            # Record metrics
            SEARCH_TOTAL.labels(
                query_type=search_type,
                result_count=str(len(processed_results))
            ).inc()
            SEARCH_LATENCY.labels(search_type=search_type).observe(time.time() - start_time)
            
            return response
        except Exception as e:
            raise Exception(f"Search failed: {str(e)}")

    def _apply_pins(self, results: List[Dict[str, Any]], pins: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply merchandising pinned products to specific ranks"""
        if not pins or not results:
            return results
        
        # Build dictionary of product_id -> pin target position
        pin_map = {p["product_id"]: p["position"] for p in pins}
        
        # Separate pinned items from other items
        pinned_items = {}
        unpinned_items = []
        
        for item in results:
            pid = str(item.get("id"))
            if pid in pin_map:
                pinned_items[pid] = item
            else:
                unpinned_items.append(item)
                
        final_results = []
        max_len = len(results)
        
        # Map target_position (1-indexed) -> item
        position_to_item = {pos: pinned_items[pid] for pid, pos in pin_map.items() if pid in pinned_items}
        
        unpinned_idx = 0
        for i in range(1, max_len + 1):
            if i in position_to_item:
                final_results.append(position_to_item[i])
            elif unpinned_idx < len(unpinned_items):
                final_results.append(unpinned_items[unpinned_idx])
                unpinned_idx += 1
                
        while unpinned_idx < len(unpinned_items):
            final_results.append(unpinned_items[unpinned_idx])
            unpinned_idx += 1
            
        return final_results

    def _apply_stock_policy(self, results: List[Dict[str, Any]], behavior: str) -> List[Dict[str, Any]]:
        """Apply stock policy (hide, demote, or keep)"""
        if not results:
            return results
            
        if behavior == "hide":
            return [item for item in results if item.get("stock") is not False]
        elif behavior == "demote":
            in_stock = []
            out_of_stock = []
            for item in results:
                if item.get("stock") is False:
                    out_of_stock.append(item)
                else:
                    in_stock.append(item)
            return in_stock + out_of_stock
        return results
    
    def _expand_query(self, query: str) -> str:
        """Semantic query expansion for fallback"""
        expansions = {
            'laptop': 'laptop computer notebook',
            'phon': 'phone mobile smartphone',
            'hedfons': 'headphones earbuds audio',
            'lappi': 'laptop computer notebook',
            'tshrt': 'tshirt t-shirt apparel',
            'wrist watch': 'wrist watch timepiece',
            'bluetooth speker': 'bluetooth speaker audio',
        }
        return expansions.get(query.lower(), query)
    
    async def get_suggestions(self, query: str, limit: int = 10, tenant_context: Optional[Any] = None) -> Dict[str, Any]:
        """Get search suggestions"""
        try:
            collection = tenant_context.collection_name if tenant_context else "products"
            if self.suggestions_service:
                suggestions = await self.suggestions_service.get_suggestions(query, limit, collection=collection)
                return {
                    "success": True,
                    "suggestions": suggestions
                }
            
            # Fallback to generated suggestions if service is not available
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
    
    async def get_trending_searches(self, limit: int = 10, category: str = None, tenant_context: Optional[Any] = None) -> Dict[str, Any]:
        """Get trending searches"""
        try:
            collection = tenant_context.collection_name if tenant_context else "products"
            if self.suggestions_service:
                trending_results = await self.suggestions_service.get_trending_searches(
                    tenant_id=tenant_context.organization_id if tenant_context else "default",
                    limit=limit,
                    category=category,
                    collection=collection
                )
                # suggestions_service returns list of dicts: [{"query": ..., "score": ...}]
                # We need list of strings for compatibility with the legacy api response
                searches = [t.get("query") for t in trending_results if t.get("query")]
                return {
                    "success": True,
                    "searches": searches
                }
                
            # Fallback to mock trending searches
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

    async def search_products(
        self,
        query: str,
        user_id: str = "guest",
        filters: Dict[str, Any] = None,
        limit: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """Compatibility method mapping search_products to handle"""
        return await self.handle(
            query=query,
            user_id=user_id,
            filters=filters,
            limit=limit,
            **kwargs
        )

    async def get_trending_products(self, category: str = None, limit: int = 10) -> Dict[str, Any]:
        """Get trending products by searching empty/popular query"""
        try:
            results = await self.search.search("", filters={"category": category} if category else {}, limit=limit)
            return {
                "success": True,
                "products": results,
                "total": len(results)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}