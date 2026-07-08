"""
Hybrid Search - Layer 4: Add-ons
Combines semantic and keyword search with variant discovery
"""
from typing import Any, Dict, List, Optional

from app.infrastructure.db.postgres import PostgresClient
from app.infrastructure.search.typesense import TypesenseClient
from app.utils.logger import get_logger

logger = get_logger("hybrid_search")


class HybridSearch:
    """Hybrid search combining semantic and keyword with variant discovery"""
    
    def __init__(self, typesense: TypesenseClient, db: PostgresClient, embeddings=None):
        self.typesense = typesense
        self.db = db
        self.embeddings = embeddings  # GeminiEmbeddings (text-embedding-002) / LocalEmbedder
        
        # Tag priority order for strict variant matching (LOCKED per requirements)
        self.VARIANT_TAG_PRIORITY = {
            # Product Identity Tags (NON-NEGOTIABLE)
            'brand': 1,
            'product_line': 2, 
            'sku_family': 3,
            # Core Type Tags
            'product_type': 4,
            'category_leaf': 5,
            # Material/Fabric (CONDITIONAL)
            'Fabric': 6,  # Required for apparel
            'Material': 6,  # Optional for FMCG
            # Pattern/Style (Lowest priority)
            'Pattern': 7,
            'Style': 7,
            # Variant Dimensions (differences allowed)
            'Size': 8,
            'Color': 8
        }
    
    async def search(
        self, 
        query: str, 
        query_vector: Optional[List[float]] = None,
        filters: Dict[str, Any] = None, 
        limit: int = 10,
        collection: str = "products"
    ) -> List[Dict[str, Any]]:
        """Hybrid search - semantic + keyword using Typesense"""
        results = []

        # Auto-embed query if no vector provided and embeddings are available
        if query_vector is None and self.embeddings and query:
            try:
                query_vector = await self.embeddings.embed_query(query)
            except Exception as e:
                logger.warning(f"Failed to embed query, falling back to keyword search: {e}")
        
        # Try Typesense hybrid search
        if query_vector and self.typesense:
            try:
                vector_q = f"embedding:({query_vector}, k:{limit})"
                res = await self.typesense.search(
                    collection=collection,
                    query=query,
                    vector_query=vector_q,
                    per_page=limit
                )
                if res.get('success'):
                    for doc in res.get('documents', []):
                        if collection != "products":
                            doc['similarity_score'] = doc.get('vector_distance', 0)
                            results.append(doc)
                        else:
                            product_id = doc.get('id')
                            if product_id:
                                product = await self.db.get_product_by_id(str(product_id))
                                if product:
                                    product['similarity_score'] = doc.get('vector_distance', 0)
                                    results.append(product)
            except Exception as e:
                logger.warning(f"Typesense hybrid search failed, falling back to keyword search: {e}")
                results = []
        
        # Fallback to Typesense keyword search
        if not results and self.typesense:
            try:
                res = await self.typesense.search(
                    collection=collection,
                    query=query,
                    per_page=limit
                )
                if res.get('success'):
                    for doc in res.get('documents', []):
                        if collection != "products":
                            results.append(doc)
                        else:
                            product_id = doc.get('id')
                            if product_id:
                                product = await self.db.get_product_by_id(str(product_id))
                                if product:
                                    results.append(product)
            except Exception as e:
                logger.warning(f"Typesense keyword search fallback failed: {e}")

        # Final fallback to direct Postgres search (only for global collection)
        if not results and collection == "products":
            results = await self.db.search_products(filters or {}, limit)
        
        return results[:limit]
    
    async def find_strict_variants(
        self, 
        product_id: str, 
        user_preferences: Optional[Dict[str, Any]] = None,
        limit: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Find strict variants of a product (same product, only size/color differences)
        Based on LOCKED tag priority order from requirements
        """
        try:
            logger.info(f"🔍 Finding strict variants for product {product_id}")
            
            # Step 1: Get the original product
            original_product = await self.db.get_product_by_id(product_id)
            if not original_product:
                logger.warning(f"Product {product_id} not found")
                return []
            
            # Step 2: Extract product identity tags (NON-NEGOTIABLE)
            identity_filters = self._extract_identity_tags(original_product)
            if not identity_filters:
                logger.warning(f"No identity tags found for product {product_id}")
                return []
            
            # Step 3: Build strict variant search filters
            variant_filters = self._build_variant_filters(original_product, identity_filters)
            
            # Step 4: Search for variants using Postgres (more reliable for exact matching)
            variant_candidates = await self.db.search_products(variant_filters, limit * 2)
            
            # Step 5: Apply strict variant validation
            strict_variants = self._validate_strict_variants(
                original_product, 
                variant_candidates,
                user_preferences
            )
            
            # Step 6: Rank variants by relevance
            ranked_variants = self._rank_variants(original_product, strict_variants, user_preferences)
            
            logger.info(f"✅ Found {len(ranked_variants)} strict variants for product {product_id}")
            return ranked_variants[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error finding variants for product {product_id}: {e}")
            return []
    
    def _extract_identity_tags(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Extract non-negotiable product identity tags"""
        identity_filters = {}
        tags = product.get('tags', {})
        
        # Brand (NON-NEGOTIABLE)
        if product.get('brand'):
            identity_filters['brand'] = product['brand']
        
        # Category (NON-NEGOTIABLE)
        if product.get('category'):
            identity_filters['category'] = product['category']
        
        # Sub-category (NON-NEGOTIABLE)
        if product.get('sub_category'):
            identity_filters['sub_category'] = product['sub_category']
        
        # Core type tags from product tags
        if tags.get('Type'):
            identity_filters['tags.Type'] = tags['Type']
        
        # Material/Fabric (CONDITIONAL - required for apparel)
        if product.get('category') == 'Clothing and Accessories':
            if tags.get('Fabric'):
                identity_filters['tags.Fabric'] = tags['Fabric']
        
        # Pattern (must match for same product)
        if tags.get('Pattern'):
            identity_filters['tags.Pattern'] = tags['Pattern']
        
        return identity_filters
    
    def _build_variant_filters(self, original_product: Dict[str, Any], identity_filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build search filters for variant discovery"""
        variant_filters = identity_filters.copy()
        
        # Exclude the original product
        variant_filters['exclude_id'] = original_product.get('id') or original_product.get('pid')
        
        # Only include products that are available (optional filter)
        variant_filters['online_available'] = True
        
        return variant_filters
    
    def _validate_strict_variants(
        self, 
        original_product: Dict[str, Any], 
        candidates: List[Dict[str, Any]],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Validate that candidates are truly strict variants"""
        strict_variants = []
        original_tags = original_product.get('tags', {})
        
        for candidate in candidates:
            # Skip if same product
            if (candidate.get('id') == original_product.get('id') or 
                candidate.get('pid') == original_product.get('pid')):
                continue
            
            candidate_tags = candidate.get('tags', {})
            
            # Validate strict variant criteria
            if self._is_strict_variant(original_tags, candidate_tags):
                # Add variant metadata
                candidate['variant_type'] = self._determine_variant_type(original_tags, candidate_tags)
                candidate['variant_differences'] = self._get_variant_differences(original_tags, candidate_tags)
                candidate['is_strict_variant'] = True
                
                strict_variants.append(candidate)
        
        return strict_variants
    
    def _is_strict_variant(self, original_tags: Dict[str, Any], candidate_tags: Dict[str, Any]) -> bool:
        """Check if candidate is a strict variant (same product, only size/color differences)"""
        
        # Core identity tags must match exactly
        identity_tags = ['Type', 'Fabric', 'Pattern', 'Fit', 'Suitable For']
        for tag in identity_tags:
            if original_tags.get(tag) != candidate_tags.get(tag):
                # Allow missing tags only if both are missing
                if original_tags.get(tag) is not None and candidate_tags.get(tag) is not None:
                    return False
        
        # Only Size and Color are allowed to differ
        allowed_differences = {'Size', 'Color', 'Brand Color', 'Secondary Color'}
        
        # Check for any non-allowed differences
        all_tags = set(original_tags.keys()) | set(candidate_tags.keys())
        for tag in all_tags:
            if tag not in allowed_differences:
                if original_tags.get(tag) != candidate_tags.get(tag):
                    # Allow None vs empty string
                    if not (original_tags.get(tag) in [None, ''] and candidate_tags.get(tag) in [None, '']):
                        return False
        
        return True
    
    def _determine_variant_type(self, original_tags: Dict[str, Any], candidate_tags: Dict[str, Any]) -> str:
        """Determine the type of variant (size, color, or both)"""
        differences = []
        
        if original_tags.get('Size') != candidate_tags.get('Size'):
            differences.append('size')
        
        if (original_tags.get('Color') != candidate_tags.get('Color') or
            original_tags.get('Brand Color') != candidate_tags.get('Brand Color')):
            differences.append('color')
        
        if len(differences) == 2:
            return 'size_and_color'
        elif 'size' in differences:
            return 'size_variant'
        elif 'color' in differences:
            return 'color_variant'
        else:
            return 'identical'
    
    def _get_variant_differences(self, original_tags: Dict[str, Any], candidate_tags: Dict[str, Any]) -> Dict[str, Any]:
        """Get specific differences between original and variant"""
        differences = {}
        
        # Size differences
        if original_tags.get('Size') != candidate_tags.get('Size'):
            differences['size'] = {
                'original': original_tags.get('Size'),
                'variant': candidate_tags.get('Size')
            }
        
        # Color differences
        if original_tags.get('Color') != candidate_tags.get('Color'):
            differences['color'] = {
                'original': original_tags.get('Color'),
                'variant': candidate_tags.get('Color')
            }
        
        return differences
    
    def _rank_variants(
        self, 
        original_product: Dict[str, Any], 
        variants: List[Dict[str, Any]],
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Rank variants by relevance and user preferences"""
        
        for variant in variants:
            score = 0.0
            
            # Base score for being a valid variant
            score += 1.0
            
            # Prefer in-stock variants
            if variant.get('stock'):
                score += 0.5
            
            # Prefer higher-rated variants
            rating = variant.get('rating', 0)
            if rating > 0:
                score += (rating / 5.0) * 0.3
            
            # Apply user preferences
            if user_preferences:
                # Preferred colors
                preferred_colors = user_preferences.get('preferred_colors', [])
                variant_color = variant.get('tags', {}).get('Color', '').lower()
                if any(color.lower() in variant_color for color in preferred_colors):
                    score += 0.4
                
                # Preferred sizes
                preferred_sizes = user_preferences.get('preferred_size', [])
                variant_size = variant.get('tags', {}).get('Size', '')
                if variant_size in preferred_sizes:
                    score += 0.3
                
                # Budget considerations
                budget_range = user_preferences.get('budget_range', {})
                variant_price = variant.get('price', {}).get('selling', 0)
                if budget_range.get('min', 0) <= variant_price <= budget_range.get('max', float('inf')):
                    score += 0.2
            
            variant['variant_score'] = score
        
        # Sort by score (highest first)
        return sorted(variants, key=lambda x: x.get('variant_score', 0), reverse=True)
    async def search_by_text(self, query: str, filters: Dict[str, Any] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Text-based search using Postgres"""
        try:
            return await self.db.search_products(filters or {}, limit)
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    async def find_substitutes(
        self, 
        product_id: str, 
        substitute_type: str = "price_focused",  # price_focused, availability_focused, quality_focused
        user_preferences: Optional[Dict[str, Any]] = None,
        limit: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Find substitute products (user-triggered only per requirements)
        Different from variants - these are alternative products serving same purpose
        """
        try:
            logger.info(f"🔄 Finding {substitute_type} substitutes for product {product_id}")
            
            # Get original product
            original_product = await self.db.get_product_by_id(product_id)
            if not original_product:
                return []
            
            # Build substitute search filters (broader than variant search)
            substitute_filters = {
                'category': original_product.get('category'),
                'sub_category': original_product.get('sub_category'),
                'exclude_id': product_id
            }
            
            # Add substitute-type specific filters
            if substitute_type == "availability_focused":
                substitute_filters['stock'] = True
                substitute_filters['online_available'] = True
            elif substitute_type == "quality_focused":
                substitute_filters['rating_min'] = 4.0
            
            # Search for substitute candidates
            candidates = await self.db.search_products(substitute_filters, limit * 3)
            
            # Rank substitutes based on type
            ranked_substitutes = self._rank_substitutes(
                original_product, 
                candidates, 
                substitute_type,
                user_preferences
            )
            
            logger.info(f"✅ Found {len(ranked_substitutes)} {substitute_type} substitutes")
            return ranked_substitutes[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error finding substitutes for product {product_id}: {e}")
            return []
    
    def _rank_substitutes(
        self, 
        original_product: Dict[str, Any], 
        candidates: List[Dict[str, Any]],
        substitute_type: str,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Rank substitute products based on substitute type"""
        
        original_price = original_product.get('price', {}).get('selling', 0)
        
        for candidate in candidates:
            score = 0.0
            candidate_price = candidate.get('price', {}).get('selling', 0)
            
            # Base score for category match
            if candidate.get('category') == original_product.get('category'):
                score += 1.0
            
            if candidate.get('sub_category') == original_product.get('sub_category'):
                score += 0.5
            
            # Type-specific scoring
            if substitute_type == "price_focused":
                # Prefer cheaper alternatives
                if candidate_price < original_price:
                    savings_ratio = (original_price - candidate_price) / original_price
                    score += savings_ratio * 2.0  # Up to 2.0 bonus for significant savings
                
            elif substitute_type == "availability_focused":
                # Prefer in-stock items
                if candidate.get('stock'):
                    score += 1.0
                if candidate.get('online_available'):
                    score += 0.5
                
            elif substitute_type == "quality_focused":
                # Prefer higher quality (rating, brand reputation)
                rating = candidate.get('rating', 0)
                if rating > original_product.get('rating', 0):
                    score += (rating - original_product.get('rating', 0)) * 0.5
            
            # Apply user preferences
            if user_preferences:
                preferred_brands = user_preferences.get('preferred_brands', [])
                if candidate.get('brand') in preferred_brands:
                    score += 0.3
                
                budget_range = user_preferences.get('budget_range', {})
                if budget_range.get('min', 0) <= candidate_price <= budget_range.get('max', float('inf')):
                    score += 0.2
            
            # Add substitute metadata
            candidate['substitute_type'] = substitute_type
            candidate['substitute_score'] = score
            candidate['price_comparison'] = self._get_price_comparison(original_product, candidate)
            candidate['is_substitute'] = True
        
        return sorted(candidates, key=lambda x: x.get('substitute_score', 0), reverse=True)
    
    def _get_price_comparison(self, original_product: Dict[str, Any], substitute: Dict[str, Any]) -> Dict[str, Any]:
        """Get price comparison between original and substitute"""
        original_price = original_product.get('price', {}).get('selling', 0)
        substitute_price = substitute.get('price', {}).get('selling', 0)
        
        if original_price > 0 and substitute_price > 0:
            difference = substitute_price - original_price
            percentage = (difference / original_price) * 100
            
            return {
                'original_price': original_price,
                'substitute_price': substitute_price,
                'difference': round(difference, 2),
                'percentage_difference': round(percentage, 1),
                'is_cheaper': difference < 0,
                'is_more_expensive': difference > 0,
                'savings': abs(difference) if difference < 0 else 0
            }
        
        return {}