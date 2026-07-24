import json

from app.container import get_container
from app.mcp.context import get_mcp_tenant_context
from app.mcp.schemas import AutocompleteQuery, SearchQuery
from app.mcp.server import mcp


@mcp.tool()
async def search_products(query: str, limit: int = 10, page: int = 1) -> str:
    """
    Search for products in the catalog using semantic or keyword search.
    """
    ctx = get_mcp_tenant_context()
    container = get_container()
    search_service = container.get("search_orchestrator")
    if not search_service:
        return json.dumps({"error": "Search service not available"})

    # Apply strict limits
    limit = min(max(limit, 1), 50)
    page = max(page, 1)

    try:
        results = await search_service.search_products(
            tenant=ctx,
            query=query,
            page=page,
            limit=limit,
            filters=None,
            user_id=None
        )
        return json.dumps([p.model_dump() for p in results.items])
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
async def search_documents(query: str, limit: int = 10, page: int = 1) -> str:
    """
    Search for documents in the tenant namespace.
    """
    ctx = get_mcp_tenant_context()
    container = get_container()
    search_service = container.get("hybrid_search")
    if not search_service:
        return json.dumps({"error": "Search service not available"})

    limit = min(max(limit, 1), 50)
    try:
        # Assuming hybrid_search has a search_documents or we use typesense directly
        # For this roadmap, we expose a read-only search documents
        # Use typesense adapter directly for documents
        typesense = container.get("typesense")
        if not typesense:
            return json.dumps({"error": "Typesense not available"})

        collection_name = f"tenant_{ctx.organization_id}_documents"
        results = await typesense.search(
            collection=collection_name,
            query=query,
            query_by="title,content",
            limit=limit,
            page=page
        )
        return json.dumps(results.get("hits", []))
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
async def autocomplete(query: str, limit: int = 5) -> str:
    """
    Get autocomplete suggestions for a partial query.
    """
    ctx = get_mcp_tenant_context()
    container = get_container()
    suggestions_service = container.get("suggestions_service")
    if not suggestions_service:
        return json.dumps({"error": "Suggestions service not available"})

    limit = min(max(limit, 1), 20)
    try:
        results = await suggestions_service.get_suggestions(
            tenant=ctx,
            query=query,
            limit=limit
        )
        return json.dumps(results)
    except Exception as e:
        return json.dumps({"error": str(e)})
