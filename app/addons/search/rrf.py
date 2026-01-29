"""
Reciprocal Rank Fusion - Layer 4: Add-ons
Combines results from multiple search engines
"""
from typing import List, Dict, Any, Optional
import math

from app.utils.logger import get_logger

logger = get_logger("rrf")


class ReciprocalRankFusion:
    """Reciprocal Rank Fusion for combining search results"""
    
    def __init__(self, k: int = 60):
        self.k = k  # Standard RRF constant
    
    def fuse_results(
        self,
        typesense_results: List[Dict[str, Any]],
        qdrant_results: List[Dict[str, Any]],
        typesense_weight: float = 0.6,
        qdrant_weight: float = 0.4
    ) -> List[Dict[str, Any]]:
        """Fuse results using RRF formula"""
        
        # Create score maps
        scores = {}
        
        # Process Typesense results
        for rank, result in enumerate(typesense_results, 1):
            product_id = result.get('id')
            if product_id:
                rrf_score = typesense_weight / (self.k + rank)
                scores[product_id] = {
                    'product': result,
                    'rrf_score': rrf_score,
                    'typesense_rank': rank,
                    'qdrant_rank': None,
                    'sources': ['typesense']
                }
        
        # Process Qdrant results
        for rank, result in enumerate(qdrant_results, 1):
            product_id = str(result.get('id'))  # Ensure string
            if product_id:
                rrf_score = qdrant_weight / (self.k + rank)
                
                if product_id in scores:
                    # Product found in both - combine scores
                    scores[product_id]['rrf_score'] += rrf_score
                    scores[product_id]['qdrant_rank'] = rank
                    scores[product_id]['sources'].append('qdrant')
                    scores[product_id]['similarity_score'] = result.get('score', 0)
                else:
                    # Product only in Qdrant
                    scores[product_id] = {
                        'product': result.get('payload', {}),
                        'rrf_score': rrf_score,
                        'typesense_rank': None,
                        'qdrant_rank': rank,
                        'similarity_score': result.get('score', 0),
                        'sources': ['qdrant']
                    }
        
        # Sort by RRF score
        fused_results = sorted(
            scores.values(),
            key=lambda x: x['rrf_score'],
            reverse=True
        )
        
        logger.info(f"Fused {len(fused_results)} results from {len(typesense_results)} Typesense + {len(qdrant_results)} Qdrant")
        
        return fused_results
    
    def rerank_by_preferences(
        self,
        results: List[Dict[str, Any]],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Rerank results based on user preferences"""
        
        if not user_preferences:
            return results
        
        for result in results:
            product = result['product']
            preference_boost = 0
            
            # Category preference
            preferred_category = user_preferences.get('favorite_category')
            if preferred_category and product.get('category') == preferred_category:
                preference_boost += 0.2
            
            # Brand preference
            preferred_brands = user_preferences.get('preferred_brands', [])
            if product.get('brand') in preferred_brands:
                preference_boost += 0.15
            
            # Price preference
            price_range = user_preferences.get('price_range', {})
            product_price = product.get('selling_price') or product.get('price', {}).get('selling', 0)
            
            if price_range:
                min_price = price_range.get('min', 0)
                max_price = price_range.get('max', float('inf'))
                
                if min_price <= product_price <= max_price:
                    preference_boost += 0.1
            
            # Apply preference boost
            result['rrf_score'] *= (1 + preference_boost)
            result['preference_boost'] = preference_boost
        
        # Re-sort by updated scores
        return sorted(results, key=lambda x: x['rrf_score'], reverse=True)
    
    def rerank_by_popularity(
        self,
        results: List[Dict[str, Any]],
        rating_weight: float = 0.3,
        stock_weight: float = 0.1
    ) -> List[Dict[str, Any]]:
        """Rerank results based on popularity signals"""
        
        for result in results:
            product = result['product']
            popularity_boost = 0
            
            # Rating boost
            rating = product.get('rating', 0)
            if rating > 4.0:
                popularity_boost += rating_weight * (rating / 5.0)
            
            # Stock availability boost
            stock = product.get('stock')
            if stock and str(stock).lower() in ['true', 'available', 'in_stock']:
                popularity_boost += stock_weight
            
            # Apply popularity boost
            result['rrf_score'] *= (1 + popularity_boost)
            result['popularity_boost'] = popularity_boost
        
        # Re-sort by updated scores
        return sorted(results, key=lambda x: x['rrf_score'], reverse=True)
    
    def get_final_results(
        self,
        fused_results: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get final formatted results"""
        
        final_results = []
        
        for i, result in enumerate(fused_results[:limit]):
            product = result['product']
            
            # Ensure product has required fields
            if not product.get('id'):
                continue
            
            final_result = {
                **product,
                'search_metadata': {
                    'rrf_score': result['rrf_score'],
                    'final_rank': i + 1,
                    'typesense_rank': result.get('typesense_rank'),
                    'qdrant_rank': result.get('qdrant_rank'),
                    'similarity_score': result.get('similarity_score'),
                    'sources': result['sources'],
                    'preference_boost': result.get('preference_boost', 0),
                    'popularity_boost': result.get('popularity_boost', 0)
                }
            }
            
            final_results.append(final_result)
        
        return final_results
