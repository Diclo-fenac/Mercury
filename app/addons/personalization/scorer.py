"""
Personalization Scorer - Layer 4: Add-ons
Enhanced behavioral personalization with cross-session and session-specific context
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.domain.users.service import UserService
from app.infrastructure.cache.redis import RedisClient
from app.utils.logger import get_logger

logger = get_logger("personalization_scorer")


class PersonalizationScorer:
    """Enhanced behavioral personalization with session context management"""
    
    def __init__(self, user_service: UserService, cache: Optional[RedisClient] = None):
        self.user_service = user_service
        self.cache = cache
        
        # Personalization weights (tunable)
        self.WEIGHTS = {
            'preferred_categories': 0.3,
            'preferred_brands': 0.25,
            'preferred_colors': 0.15,
            'budget_range': 0.2,
            'session_constraints': 0.4,  # Session rules override long-term preferences
            'behavioral_patterns': 0.2,
            'availability_preference': 0.1
        }
    
    async def score_products(
        self, 
        user_id: str, 
        products: List[Dict[str, Any]],
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Enhanced behavioral scoring with session context"""
        try:
            logger.info(f"🎯 Scoring {len(products)} products for user {user_id}")
            
            # Get behavioral context (Firestore + Redis merge)
            context = await self.get_behavioral_context(user_id, session_id)
            
            if not context:
                logger.warning(f"No personalization context for user {user_id}")
                return products
            
            # Score each product
            scored_products = []
            for product in products:
                score = await self._calculate_product_score(product, context)
                product['personalization_score'] = score
                product['personalization_applied'] = True
                product['personalization_context'] = {
                    'session_constraints_applied': bool(context.get('session_constraints')),
                    'long_term_preferences_applied': bool(context.get('long_term_preferences')),
                    'behavioral_patterns_applied': bool(context.get('behavioral_patterns'))
                }
                scored_products.append(product)
            
            # Sort by personalization score
            ranked_products = sorted(scored_products, key=lambda x: x['personalization_score'], reverse=True)
            
            logger.info(f"✅ Products scored and ranked for user {user_id}")
            return ranked_products
            
        except Exception as e:
            logger.error(f"❌ Error scoring products for user {user_id}: {e}")
            return products
    
    async def get_behavioral_context(self, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Build behavioral context using Firestore + Redis merge logic
        Session constraints (Redis) override long-term preferences (Firestore)
        """
        try:
            # Step 1: Get long-term preferences from Firestore (hints)
            long_term_context = await self._get_long_term_context(user_id)
            
            # Step 2: Get session constraints from Redis (rules)
            session_context = await self._get_session_context(user_id, session_id)
            
            # Step 3: Get cross-session snapshot from Redis (read-optimized)
            cross_session_context = await self._get_cross_session_context(user_id)
            
            # Step 4: Merge contexts with session rules taking precedence
            merged_context = self._merge_contexts(long_term_context, session_context, cross_session_context)
            
            logger.info(f"📊 Built behavioral context for user {user_id}")
            return merged_context
            
        except Exception as e:
            logger.error(f"❌ Error building behavioral context for user {user_id}: {e}")
            return {}
    
    async def _get_long_term_context(self, user_id: str) -> Dict[str, Any]:
        """Get long-term preferences from Firestore (hints)"""
        try:
            profile = await self.user_service.get_user_profile(user_id)
            if not profile:
                return {}
            
            return {
                'preferences': profile.get('preferences', {}),
                'behavior': profile.get('behavior', {}),
                'stats': profile.get('stats', {}),
                'source': 'firestore_long_term'
            }
            
        except Exception as e:
            logger.error(f"Error getting long-term context: {e}")
            return {}
    
    async def _get_session_context(self, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get session constraints from Redis (rules)"""
        if not self.cache or not session_id:
            return {}
        
        try:
            # session:{user_id}:{session_id} - Session constraints (rules)
            session_key = f"session:{user_id}:{session_id}"
            session_data = await self.cache.get_json(session_key)
            
            if session_data:
                return {
                    'constraints': session_data,
                    'source': 'redis_session_rules',
                    'session_id': session_id
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting session context: {e}")
            return {}
    
    async def _get_cross_session_context(self, user_id: str) -> Dict[str, Any]:
        """Get cross-session snapshot from Redis (read-optimized)"""
        if not self.cache:
            return {}
        
        try:
            # user_context:{user_id} - Cross-session hints (read-optimized)
            context_key = f"user_context:{user_id}"
            context_data = await self.cache.get_json(context_key)
            
            if context_data:
                return {
                    'cross_session_hints': context_data,
                    'source': 'redis_cross_session',
                    'last_updated': context_data.get('last_updated')
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting cross-session context: {e}")
            return {}
    
    def _merge_contexts(
        self, 
        long_term: Dict[str, Any], 
        session: Dict[str, Any], 
        cross_session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge contexts with session rules overriding long-term preferences
        Example: "User prefers Amul (firestore) but session says vegan (Redis) → suggest soy alternatives"
        """
        merged = {
            'long_term_preferences': long_term.get('preferences', {}),
            'behavioral_patterns': long_term.get('behavior', {}),
            'user_stats': long_term.get('stats', {}),
            'session_constraints': session.get('constraints', {}),
            'cross_session_hints': cross_session.get('cross_session_hints', {}),
            'reasoning': []
        }
        
        # Apply session constraint logic
        session_constraints = merged['session_constraints']
        long_term_prefs = merged['long_term_preferences']
        
        # Example reasoning patterns
        if session_constraints.get('dietary_restrictions'):
            dietary = session_constraints['dietary_restrictions']
            if 'vegan' in dietary and 'Amul' in long_term_prefs.get('preferred_brands', []):
                merged['reasoning'].append("User prefers Amul but session requires vegan → suggest soy alternatives")
                # Override brand preferences for this session
                merged['effective_brands'] = [b for b in long_term_prefs.get('preferred_brands', []) 
                                            if b.lower() not in ['amul', 'dairy']]
                merged['effective_brands'].extend(['silk', 'oatly', 'alpro'])  # Vegan alternatives
        
        if session_constraints.get('budget_override'):
            budget_override = session_constraints['budget_override']
            original_budget = long_term_prefs.get('budget_range', {})
            merged['reasoning'].append(f"Session budget override: {budget_override} vs long-term {original_budget}")
            merged['effective_budget'] = budget_override
        else:
            merged['effective_budget'] = long_term_prefs.get('budget_range', {})
        
        if session_constraints.get('size_filter'):
            size_filter = session_constraints['size_filter']
            merged['reasoning'].append(f"Session size constraint: {size_filter}")
            merged['effective_sizes'] = size_filter if isinstance(size_filter, list) else [size_filter]
        else:
            merged['effective_sizes'] = long_term_prefs.get('preferred_size', [])
        
        return merged
    
    async def _calculate_product_score(self, product: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate personalization score for a product"""
        base_score = 1.0
        
        # Session constraints (highest priority)
        session_score = self._apply_session_constraints(product, context.get('session_constraints', {}))
        
        # Long-term preferences (hints)
        preference_score = self._apply_long_term_preferences(product, context.get('long_term_preferences', {}))
        
        # Behavioral patterns
        behavioral_score = self._apply_behavioral_patterns(product, context.get('behavioral_patterns', {}))
        
        # Effective preferences (merged)
        effective_score = self._apply_effective_preferences(product, context)
        
        # Combine scores with weights
        final_score = (
            base_score +
            (session_score * self.WEIGHTS['session_constraints']) +
            (preference_score * self.WEIGHTS['preferred_categories']) +
            (behavioral_score * self.WEIGHTS['behavioral_patterns']) +
            (effective_score * 0.3)
        )
        
        return round(final_score, 3)
    
    def _apply_session_constraints(self, product: Dict[str, Any], constraints: Dict[str, Any]) -> float:
        """Apply session constraints (rules that override preferences)"""
        score = 0.0
        
        # Dietary restrictions
        dietary = constraints.get('dietary_restrictions', [])
        if 'vegan' in dietary:
            # Boost vegan products, penalize dairy
            if 'vegan' in product.get('title', '').lower() or 'soy' in product.get('title', '').lower():
                score += 1.0
            elif any(dairy in product.get('brand', '').lower() for dairy in ['amul', 'dairy', 'milk']):
                score -= 2.0  # Strong penalty for dairy when vegan required
        
        # Budget override
        budget_override = constraints.get('budget_override', {})
        if budget_override:
            product_price = product.get('price', {}).get('selling', 0)
            min_price = budget_override.get('min', 0)
            max_price = budget_override.get('max', float('inf'))
            
            if min_price <= product_price <= max_price:
                score += 0.5
            else:
                score -= 1.0  # Penalty for out of budget
        
        # Size filter
        size_filter = constraints.get('size_filter')
        if size_filter:
            product_size = product.get('tags', {}).get('Size')
            if product_size in (size_filter if isinstance(size_filter, list) else [size_filter]):
                score += 0.5
        
        return score
    
    def _apply_long_term_preferences(self, product: Dict[str, Any], preferences: Dict[str, Any]) -> float:
        """Apply long-term preferences (hints)"""
        score = 0.0
        
        # Preferred categories
        preferred_categories = preferences.get('preferred_categories', [])
        if product.get('category') in preferred_categories:
            score += 0.3
        
        # Preferred brands
        preferred_brands = preferences.get('preferred_brands', [])
        if product.get('brand') in preferred_brands:
            score += 0.25
        
        # Preferred colors
        preferred_colors = preferences.get('preferred_colors', [])
        product_color = product.get('tags', {}).get('Color', '').lower()
        if any(color.lower() in product_color for color in preferred_colors):
            score += 0.15
        
        return score
    
    def _apply_behavioral_patterns(self, product: Dict[str, Any], behavior: Dict[str, Any]) -> float:
        """Apply behavioral patterns"""
        score = 0.0
        
        # Frequent categories
        frequent_categories = behavior.get('frequent_categories', [])
        if product.get('category') in frequent_categories:
            score += 0.2
        
        # Most viewed products (similar products)
        most_viewed = behavior.get('most_viewed_products', [])
        if product.get('id') in most_viewed or product.get('pid') in most_viewed:
            score += 0.3
        
        return score
    
    def _apply_effective_preferences(self, product: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Apply effective preferences (merged context)"""
        score = 0.0
        
        # Effective brands (after session constraints)
        effective_brands = context.get('effective_brands', context.get('long_term_preferences', {}).get('preferred_brands', []))
        if product.get('brand') in effective_brands:
            score += 0.2
        
        # Effective budget
        effective_budget = context.get('effective_budget', {})
        if effective_budget:
            product_price = product.get('price', {}).get('selling', 0)
            min_price = effective_budget.get('min', 0)
            max_price = effective_budget.get('max', float('inf'))
            
            if min_price <= product_price <= max_price:
                score += 0.15
        
        # Effective sizes
        effective_sizes = context.get('effective_sizes', [])
        if effective_sizes:
            product_size = product.get('tags', {}).get('Size')
            if product_size in effective_sizes:
                score += 0.1
        
        return score
    
    async def save_session_constraints(
        self, 
        user_id: str, 
        session_id: str, 
        constraints: Dict[str, Any],
        ttl: int = 3600
    ) -> bool:
        """Save session constraints to Redis"""
        if not self.cache:
            return False
        
        try:
            session_key = f"session:{user_id}:{session_id}"
            constraints['created_at'] = datetime.now().isoformat()
            constraints['ttl'] = ttl
            
            await self.cache.set_json(session_key, constraints, ttl)
            logger.info(f"💾 Saved session constraints for user {user_id}, session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving session constraints: {e}")
            return False
    
    async def update_cross_session_context(self, user_id: str, context_update: Dict[str, Any]) -> bool:
        """Update cross-session context snapshot"""
        if not self.cache:
            return False
        
        try:
            context_key = f"user_context:{user_id}"
            
            # Get existing context
            existing_context = await self.cache.get_json(context_key) or {}
            
            # Merge with update
            existing_context.update(context_update)
            existing_context['last_updated'] = datetime.now().isoformat()
            
            # Save with longer TTL (24 hours)
            await self.cache.set_json(context_key, existing_context, 86400)
            logger.info(f"🔄 Updated cross-session context for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating cross-session context: {e}")
            return False
