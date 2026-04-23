"""
Personalization Tools - Layer 3: Intelligence
Function calling tools for behavioral personalization and context management
"""
from typing import Any, Dict, List, Optional

from app.addons.personalization.scorer import PersonalizationScorer
from app.utils.logger import get_logger

logger = get_logger("personalization_tools")


class PersonalizationTools:
    """Behavioral personalization tools for LLM function calling"""
    
    def __init__(self, personalization_scorer: PersonalizationScorer):
        self.scorer = personalization_scorer
    
    async def apply_behavioral_personalization(
        self,
        user_id: str,
        products: List[Dict[str, Any]],
        session_id: Optional[str] = None,
        context_hints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Apply behavioral personalization to product list
        Automatic execution - enhances all product recommendations
        """
        try:
            logger.info(f"🎯 Applying behavioral personalization for user {user_id}")
            
            if not products:
                return {
                    "success": True,
                    "user_id": user_id,
                    "products_processed": 0,
                    "personalized_products": [],
                    "personalization_applied": False,
                    "message": "No products to personalize"
                }
            
            # Apply behavioral scoring
            personalized_products = await self.scorer.score_products(
                user_id, 
                products.copy(),  # Don't modify original list
                session_id
            )
            
            # Extract personalization insights
            insights = self._extract_personalization_insights(personalized_products)
            
            logger.info(f"✅ Personalized {len(personalized_products)} products for user {user_id}")
            
            return {
                "success": True,
                "user_id": user_id,
                "session_id": session_id,
                "products_processed": len(products),
                "personalized_products": personalized_products,
                "personalization_applied": True,
                "insights": insights,
                "execution_type": "automatic",
                "user_message": f"Personalized {len(products)} products based on your preferences and current session."
            }
            
        except Exception as e:
            logger.error(f"❌ Error applying personalization for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "products_processed": len(products) if products else 0,
                "personalized_products": products or [],
                "personalization_applied": False
            }
    
    async def set_session_constraints(
        self,
        user_id: str,
        session_id: str,
        constraints: Dict[str, Any],
        ttl: int = 3600
    ) -> Dict[str, Any]:
        """
        Set session-specific constraints that override long-term preferences
        Example: dietary restrictions, budget overrides, size filters
        """
        try:
            logger.info(f"📝 Setting session constraints for user {user_id}, session {session_id}")
            
            # Validate constraints
            validated_constraints = self._validate_session_constraints(constraints)
            
            # Save to Redis
            success = await self.scorer.save_session_constraints(
                user_id, 
                session_id, 
                validated_constraints,
                ttl
            )
            
            if success:
                # Generate reasoning explanation
                reasoning = self._generate_constraint_reasoning(validated_constraints)
                
                return {
                    "success": True,
                    "user_id": user_id,
                    "session_id": session_id,
                    "constraints_set": validated_constraints,
                    "ttl": ttl,
                    "reasoning": reasoning,
                    "user_message": f"Session preferences updated: {reasoning}"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to save session constraints",
                    "user_id": user_id,
                    "session_id": session_id
                }
            
        except Exception as e:
            logger.error(f"❌ Error setting session constraints: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "session_id": session_id
            }
    
    async def get_behavioral_context(
        self,
        user_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive behavioral context for user
        Shows how session constraints override long-term preferences
        """
        try:
            logger.info(f"📊 Getting behavioral context for user {user_id}")
            
            context = await self.scorer.get_behavioral_context(user_id, session_id)
            
            if not context:
                return {
                    "success": True,
                    "user_id": user_id,
                    "context_available": False,
                    "message": "No behavioral context available for this user"
                }
            
            # Format context for LLM understanding
            formatted_context = self._format_context_for_llm(context)
            
            return {
                "success": True,
                "user_id": user_id,
                "session_id": session_id,
                "context_available": True,
                "behavioral_context": formatted_context,
                "reasoning": context.get('reasoning', []),
                "context_sources": {
                    "long_term_preferences": bool(context.get('long_term_preferences')),
                    "session_constraints": bool(context.get('session_constraints')),
                    "cross_session_hints": bool(context.get('cross_session_hints'))
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting behavioral context: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id,
                "context_available": False
            }
    
    async def update_user_context_snapshot(
        self,
        user_id: str,
        context_update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update cross-session context snapshot
        Used to maintain read-optimized user context
        """
        try:
            logger.info(f"🔄 Updating context snapshot for user {user_id}")
            
            success = await self.scorer.update_cross_session_context(user_id, context_update)
            
            if success:
                return {
                    "success": True,
                    "user_id": user_id,
                    "context_updated": context_update,
                    "user_message": "Your preferences have been updated for future sessions."
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to update context snapshot",
                    "user_id": user_id
                }
            
        except Exception as e:
            logger.error(f"❌ Error updating context snapshot: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }
    
    def _extract_personalization_insights(self, personalized_products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract insights from personalized products"""
        insights = {
            "total_products": len(personalized_products),
            "personalization_applied_count": 0,
            "average_score": 0.0,
            "top_scoring_categories": [],
            "personalization_factors": []
        }
        
        scores = []
        categories = {}
        
        for product in personalized_products:
            if product.get('personalization_applied'):
                insights["personalization_applied_count"] += 1
                
                score = product.get('personalization_score', 1.0)
                scores.append(score)
                
                category = product.get('category', 'Unknown')
                categories[category] = categories.get(category, 0) + 1
                
                # Extract personalization context
                context = product.get('personalization_context', {})
                if context.get('session_constraints_applied'):
                    insights["personalization_factors"].append("session_constraints")
                if context.get('long_term_preferences_applied'):
                    insights["personalization_factors"].append("long_term_preferences")
                if context.get('behavioral_patterns_applied'):
                    insights["personalization_factors"].append("behavioral_patterns")
        
        # Calculate averages and top categories
        if scores:
            insights["average_score"] = round(sum(scores) / len(scores), 3)
        
        insights["top_scoring_categories"] = sorted(
            categories.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        # Remove duplicates from factors
        insights["personalization_factors"] = list(set(insights["personalization_factors"]))
        
        return insights
    
    def _validate_session_constraints(self, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean session constraints"""
        validated = {}
        
        # Dietary restrictions
        if 'dietary_restrictions' in constraints:
            dietary = constraints['dietary_restrictions']
            if isinstance(dietary, list):
                validated['dietary_restrictions'] = [d.lower() for d in dietary if isinstance(d, str)]
            elif isinstance(dietary, str):
                validated['dietary_restrictions'] = [dietary.lower()]
        
        # Budget override
        if 'budget_override' in constraints:
            budget = constraints['budget_override']
            if isinstance(budget, dict) and 'min' in budget and 'max' in budget:
                validated['budget_override'] = {
                    'min': max(0, float(budget['min'])),
                    'max': max(0, float(budget['max']))
                }
        
        # Size filter
        if 'size_filter' in constraints:
            size_filter = constraints['size_filter']
            if isinstance(size_filter, (list, str)):
                validated['size_filter'] = size_filter
        
        # Color preferences (session-specific)
        if 'color_preferences' in constraints:
            colors = constraints['color_preferences']
            if isinstance(colors, list):
                validated['color_preferences'] = colors
        
        return validated
    
    def _generate_constraint_reasoning(self, constraints: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for constraints"""
        reasons = []
        
        if constraints.get('dietary_restrictions'):
            dietary = constraints['dietary_restrictions']
            reasons.append(f"dietary preferences set to {', '.join(dietary)}")
        
        if constraints.get('budget_override'):
            budget = constraints['budget_override']
            reasons.append(f"budget range set to ${budget['min']}-${budget['max']}")
        
        if constraints.get('size_filter'):
            size_filter = constraints['size_filter']
            if isinstance(size_filter, list):
                reasons.append(f"size preferences set to {', '.join(size_filter)}")
            else:
                reasons.append(f"size preference set to {size_filter}")
        
        return "; ".join(reasons) if reasons else "session preferences updated"
    
    def _format_context_for_llm(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Format behavioral context for LLM understanding"""
        formatted = {
            "personalization_active": True,
            "context_sources": []
        }
        
        # Long-term preferences (hints)
        long_term = context.get('long_term_preferences', {})
        if long_term:
            formatted["long_term_preferences"] = {
                "preferred_categories": long_term.get('preferred_categories', []),
                "preferred_brands": long_term.get('preferred_brands', []),
                "preferred_colors": long_term.get('preferred_colors', []),
                "budget_range": long_term.get('budget_range', {}),
                "source": "firestore_profile"
            }
            formatted["context_sources"].append("long_term_preferences")
        
        # Session constraints (rules)
        session = context.get('session_constraints', {})
        if session:
            formatted["session_constraints"] = session
            formatted["context_sources"].append("session_constraints")
        
        # Effective preferences (merged)
        if context.get('effective_brands'):
            formatted["effective_preferences"] = {
                "brands": context.get('effective_brands', []),
                "budget": context.get('effective_budget', {}),
                "sizes": context.get('effective_sizes', [])
            }
        
        # Reasoning
        if context.get('reasoning'):
            formatted["personalization_reasoning"] = context['reasoning']
        
        return formatted
    
    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions for LLM registration"""
        return {
            "apply_behavioral_personalization": {
                "description": "Apply behavioral personalization to product recommendations. Executes automatically for all product lists.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID for personalization"
                        },
                        "products": {
                            "type": "array",
                            "description": "List of products to personalize",
                            "items": {"type": "object"}
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Optional session ID for session-specific constraints"
                        },
                        "context_hints": {
                            "type": "object",
                            "description": "Optional additional context hints"
                        }
                    },
                    "required": ["user_id", "products"]
                }
            },
            "set_session_constraints": {
                "description": "Set session-specific constraints that override long-term preferences (dietary, budget, size filters).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Session ID"
                        },
                        "constraints": {
                            "type": "object",
                            "description": "Session constraints",
                            "properties": {
                                "dietary_restrictions": {"type": "array", "items": {"type": "string"}},
                                "budget_override": {"type": "object", "properties": {"min": {"type": "number"}, "max": {"type": "number"}}},
                                "size_filter": {"type": ["string", "array"]},
                                "color_preferences": {"type": "array", "items": {"type": "string"}}
                            }
                        },
                        "ttl": {
                            "type": "integer",
                            "description": "Time to live in seconds",
                            "default": 3600
                        }
                    },
                    "required": ["user_id", "session_id", "constraints"]
                }
            },
            "get_behavioral_context": {
                "description": "Get comprehensive behavioral context showing how session constraints override long-term preferences.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "string",
                            "description": "User ID"
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Optional session ID"
                        }
                    },
                    "required": ["user_id"]
                }
            }
        }