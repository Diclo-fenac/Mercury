"""
Recommendation Orchestrator - Layer 2: Orchestration
Coordinates recommendation workflow
"""
from typing import Any, Dict, Optional

from app.domain.products.service import ProductService
from app.domain.recommendations.engine import RecommendationEngine
from app.domain.users.service import UserService


class RecommendationOrchestrator:
    """Orchestrates recommendation workflow"""

    def __init__(
        self,
        recommendation_engine: RecommendationEngine,
        user_service: UserService,
        product_service: ProductService
    ):
        self.recommendations = recommendation_engine
        self.users = user_service
        self.products = product_service

    async def get_personalized_recommendations(
        self,
        organization_id: str,
        user_id: str,
        limit: int = 10,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get personalized recommendations for user"""
        try:
            # Get user profile for personalization
            user_profile = await self.users.get_user_profile(organization_id, user_id)

            if not user_profile:
                # Return generic recommendations for new users
                filters = {"category": category} if category else {}
                products = await self.products.search_products(organization_id, filters, limit)

                return {
                    "success": True,
                    "recommendations": products,
                    "personalization_type": "generic",
                    "strategies_used": ["popular_products"]
                }

            # Get personalized recommendations using the engine
            recommendations = await self.recommendations.get_personalized_recommendations(
                organization_id, user_id, limit
            )

            # Filter by category if specified
            if category:
                recommendations = [r for r in recommendations if r.get('category') == category]

            return {
                "success": True,
                "recommendations": recommendations[:limit],
                "personalization_type": "preference_based",
                "strategies_used": ["user_preferences", "category_affinity"]
            }

        except Exception as e:
            raise Exception(f"Failed to get personalized recommendations: {str(e)}")

    async def get_product_recommendations(
        self,
        product_id: str,
        organization_id: str,
        user_id: Optional[str] = None,
        recommendation_type: str = "similar",
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get product-based recommendations"""
        try:
            # Get the source product
            source_product = await self.products.get_product(organization_id, product_id)

            if not source_product:
                return {"success": False, "error": "not_found"}

            if recommendation_type == "similar":
                recommendations = await self.recommendations.get_similar_products(
                    organization_id, product_id, limit
                )
            elif recommendation_type == "fbt":
                recommendations = await self.recommendations.get_frequently_bought_together(
                    organization_id, product_id, limit
                )
            elif recommendation_type == "complementary":
                recommendations = await self.recommendations.get_complementary_products(
                    organization_id, product_id, limit
                )
            elif recommendation_type == "substitute":
                recommendations = await self.recommendations.get_substitute_products(
                    organization_id, product_id, limit
                )
            else:
                # For other types, use similar products as fallback
                recommendations = await self.recommendations.get_similar_products(
                    organization_id, product_id, limit
                )

            return {
                "success": True,
                "recommendations": recommendations
            }

        except Exception as e:
            raise Exception(f"Failed to get product recommendations: {str(e)}")
