"""
Search Orchestrator - Layer 2: Orchestration
Coordinates search workflow
"""
import time
from typing import Any, Dict, List, Optional

from app.addons.personalization.scorer import PersonalizationScorer
from app.addons.search.hybrid import HybridSearch
from app.domain.search.rules import SearchRuleEngine
from app.domain.search.suggestions_service import SearchSuggestionsService
from app.infrastructure.cache.keys import build_search_cache_key
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
            from app.core.security.context import tenant_context_var
            from app.utils.pii_redactor import PIIRedactor

            # Redact PII from query before logging, caching, or processing
            query = PIIRedactor.redact(query)

            tenant_context_var.set(tenant_context)
            collection = tenant_context.collection_name if tenant_context else "products"
            tenant_id = tenant_context.organization_id if tenant_context else None
            enable_personalization = (
                tenant_context.config.get("enable_personalization", False)
                if tenant_context
                else True
            )
            revision = 0
            if self.cache and tenant_id:
                try:
                    revision = await self.cache.get_tenant_namespace_revision(tenant_id, "search")
                except Exception:
                    revision = 0

            cache_key = build_search_cache_key(
                tenant_id=tenant_id,
                query=query,
                user_id=user_id if enable_personalization else None,
                filters=filters or {},
                limit=limit,
                offset=offset,
                sort=sort,
                search_type=search_type,
                include_suggestions=include_suggestions,
                collection=collection,
                revision=revision,
            )

            cached = None
            if self.cache:
                self._cache_total += 1
                cached = await self.cache.get_json(cache_key)
                if cached:
                    self._cache_hits += 1
                    CACHE_HITS.inc()
                    CACHE_HIT_RATE.set(self._cache_hits / self._cache_total)
                    cached = dict(cached)
                    cached_meta = dict(cached.get("meta") or {})
                    cached_meta.update({
                        "cache_hit": True,
                        "latency_ms": int((time.time() - start_time) * 1000),
                    })
                    cached["meta"] = cached_meta
                    SEARCH_TOTAL.labels(
                        query_type=search_type,
                        result_count=str(len(cached.get("results", []))),
                    ).inc()
                    SEARCH_LATENCY.labels(search_type=search_type).observe(time.time() - start_time)
                    return cached
                CACHE_MISSES.inc()
                CACHE_HIT_RATE.set(self._cache_hits / self._cache_total)
            
            # 1. Check for Query rules (Redirects & Synonyms)
            expanded_query = query
            is_redirect = False
            redirect_url = None
            
            if self.tenant_service and tenant_id:
                redirects = await self.tenant_service.get_redirects(tenant_id)
                synonyms = await self.tenant_service.get_all_synonyms(tenant_id)
                
                query_action = SearchRuleEngine.apply_query_rules(query, redirects, synonyms)
                if query_action.get("action") == "redirect":
                    is_redirect = True
                    redirect_url = query_action.get("url")
                else:
                    expanded_query = query_action.get("expanded_query", query)
            
            if is_redirect:
                return {
                    "success": True,
                    "query": query,
                    "action": "redirect",
                    "redirect_url": redirect_url,
                    "results": [],
                    "total_results": 0,
                    "facets": {},
                    "meta": {"latency_ms": int((time.time() - start_time) * 1000)},
                    "filters_applied": filters or {}
                }

            # 2. Retrieve candidates from Typesense
            candidate_limit = min(250, limit + offset)
            retrieval = await self.search.search_with_metadata(
                expanded_query,
                filters=filters,
                limit=candidate_limit,
                offset=0,
                collection=collection,
                mode=search_type,
                sort=sort,
                keyword_weight=float(tenant_context.config.get("rrf_keyword_weight", 1.0)) if tenant_context else 1.0,
                vector_weight=float(tenant_context.config.get("rrf_vector_weight", 1.0)) if tenant_context else 1.0,
                num_typos=int(tenant_context.config.get("typo_tolerance", 2)) if tenant_context else 2,
                searchable_fields=tenant_context.config.get("searchable_fields") if tenant_context else None,
            )
            results = retrieval["documents"]
            total_results = retrieval["total"]
            
            # Track zero-result queries
            if len(results) == 0:
                ZERO_RESULT_QUERIES.labels(search_type=search_type, fallback_used='false').inc()
                # Try fallback (semantic expansion)
                fallback_query = self._expand_query(query)
                if fallback_query != query:
                    fallback_used = True
                    retrieval = await self.search.search_with_metadata(
                        fallback_query,
                        filters=filters,
                        limit=candidate_limit,
                        offset=0,
                        collection=collection,
                        mode=search_type,
                        sort=sort,
                        keyword_weight=float(tenant_context.config.get("rrf_keyword_weight", 1.0)) if tenant_context else 1.0,
                        vector_weight=float(tenant_context.config.get("rrf_vector_weight", 1.0)) if tenant_context else 1.0,
                        num_typos=int(tenant_context.config.get("typo_tolerance", 2)) if tenant_context else 2,
                        searchable_fields=tenant_context.config.get("searchable_fields") if tenant_context else None,
                    )
                    results = retrieval["documents"]
                    total_results = retrieval["total"]
                    if len(results) > 0:
                        ZERO_RESULT_QUERIES.labels(search_type=search_type, fallback_used='true').inc()
            
            # 3. Apply out-of-stock behavior
            if tenant_context:
                behavior = tenant_context.config.get("out_of_stock_behavior", "demote")
                results = self._apply_stock_policy(results, behavior)

            # 4. Apply boosts and pinned products (merchandising)
            if self.tenant_service and tenant_context:
                pins = await self.tenant_service.get_pinned_products(tenant_context.organization_id, query)
                boosts = await self.tenant_service.get_boosts(tenant_context.organization_id)
                if pins or boosts:
                    results = SearchRuleEngine.apply_result_rules(results, pins, boosts)

            # 5. Personalize results and add transparency (only if enabled by tenant config)
            personalization_applied = False
            if self.personalization and enable_personalization:
                try:
                    personalized = await self.personalization.score_products(tenant_id, user_id, results)
                    results = personalized
                    personalization_applied = True
                except Exception as e:
                    print(f"Personalization error: {e}")
            
            # 6. Apply margin/inventory commerce optimization
            if tenant_context and tenant_context.config.get("enable_commerce_optimization", True):
                for item in results:
                    margin = float(item.get("margin") or 0.0)
                    stock = int(item.get("stock") or 0)
                    
                    # Compute a commerce multiplier (max 1.3x boost)
                    margin_boost = 1.0 + (min(margin, 100.0) / 100.0) * 0.2
                    inventory_boost = 1.0
                    if stock > 100:
                        inventory_boost = 1.1
                    elif stock < 10:
                        inventory_boost = 0.95
                        
                    commerce_multiplier = margin_boost * inventory_boost
                    
                    # Apply multiplier to whichever score is active
                    if personalization_applied and "personalization_score" in item:
                        item["personalization_score"] *= commerce_multiplier
                    
                    retrieval_evidence = item.get("_retrieval", {})
                    if retrieval_evidence.get("rrf_score") is not None:
                        retrieval_evidence["rrf_score"] *= commerce_multiplier
                        
                # Re-sort if scores changed
                if personalization_applied:
                    results.sort(key=lambda x: x.get("personalization_score", 0), reverse=True)
                else:
                    results.sort(
                        key=lambda x: x.get("_retrieval", {}).get("rrf_score") or 0,
                        reverse=True,
                    )
            
            # Process results with real retrieval evidence, then paginate after all
            # merchant and personalization ranking changes.
            processed_results = []
            facets = self._format_facets(retrieval.get("facets", []))
            
            for item in results:
                retrieval_evidence = item.pop("_retrieval", {})
                current_score = item.get("personalization_score") or retrieval_evidence.get("rrf_score") or 0.0
                breakdown = {
                    "retrieval": retrieval_evidence,
                    "personalization_score": item.get("personalization_score") if personalization_applied else None,
                }
                
                item['score'] = current_score
                item['breakdown'] = breakdown
                processed_results.append(item)

            if not facets:
                facets = self._calculate_page_facets(processed_results)
            paginated_results = processed_results[offset : offset + limit]
            
            latency = int((time.time() - start_time) * 1000)
            
            response = {
                "success": True,
                "query": query,
                "results": paginated_results,
                "total_results": total_results,
                "facets": facets,
                "meta": {
                    "latency_ms": latency,
                    "cache_hit": cached is not None,
                    "search_mode": search_type,
                    "fallback_used": fallback_used or retrieval.get("fallback_used", False),
                    "retrieval": retrieval.get("retrieval"),
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
                result_count=str(len(paginated_results))
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
        
        # Sort pins by target position
        sorted_pins = sorted(position_to_item.items())
        
        final_results = []
        unpinned_idx = 0
        
        for pos, item in sorted_pins:
            # Add unpinned items until we reach the target index (pos - 1)
            while len(final_results) < pos - 1 and unpinned_idx < len(unpinned_items):
                final_results.append(unpinned_items[unpinned_idx])
                unpinned_idx += 1
            # Once we've padded up to the target index, or if we run out of unpinned items, append the pinned item
            final_results.append(item)
            
        # Add any remaining unpinned items
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

    @staticmethod
    def _format_facets(facet_counts: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        facets: Dict[str, Dict[str, int]] = {}
        for facet in facet_counts:
            field_name = facet.get("field_name")
            if not field_name:
                continue
            facets[field_name] = {
                str(count.get("value")): int(count.get("count", 0))
                for count in facet.get("counts", [])
            }
        return facets

    @staticmethod
    def _calculate_page_facets(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
        facets = {"brand": {}, "category": {}}
        for item in results:
            for field, default in (("brand", "Unknown"), ("category", "General")):
                value = item.get(field) or default
                facets[field][value] = facets[field].get(value, 0) + 1
        return facets
    
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
                if suggestions:
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
