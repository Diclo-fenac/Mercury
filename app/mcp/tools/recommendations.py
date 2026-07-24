import json

from app.container import get_container
from app.mcp.context import get_mcp_tenant_context
from app.mcp.server import mcp


@mcp.tool()
async def find_similar_products(product_id: str, limit: int = 5) -> str:
    """
    Find products similar to a given product ID.
    """
    ctx = get_mcp_tenant_context()
    container = get_container()
    recommendation_engine = container.get("recommendation_engine")

    if not recommendation_engine:
        return json.dumps({"error": "Recommendation engine not available"})

    limit = min(max(limit, 1), 20)
    try:
        results = await recommendation_engine.get_similar_products(
            tenant=ctx,
            product_id=product_id,
            limit=limit
        )
        return json.dumps([p.model_dump() for p in results])
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
async def recommend_products(user_id: str, limit: int = 5) -> str:
    """
    Get personalized product recommendations for a user.
    """
    ctx = get_mcp_tenant_context()
    container = get_container()
    recommendation_orchestrator = container.get("recommendation_orchestrator")

    if not recommendation_orchestrator:
        return json.dumps({"error": "Recommendation orchestrator not available"})

    limit = min(max(limit, 1), 20)
    try:
        # Assuming the orchestrator has a get_recommendations_for_user method
        # If not, fallback to trending or personalized scoring
        # (This is just an interface bridge)
        results = await recommendation_orchestrator.get_personalized_recommendations(
            tenant=ctx,
            user_id=user_id,
            limit=limit,
            context={}
        )
        return json.dumps([p.model_dump() for p in results.items])
    except Exception as e:
        return json.dumps({"error": str(e)})
