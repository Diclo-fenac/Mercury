import json

from app.container import get_container
from app.mcp.context import get_mcp_tenant_context
from app.mcp.server import mcp


@mcp.tool()
async def get_product(product_id: str) -> str:
    """
    Get a specific product by its ID from the catalog.
    """
    ctx = get_mcp_tenant_context()
    container = get_container()
    product_service = container.get("product_service")
    if not product_service:
        return json.dumps({"error": "Product service not available"})

    try:
        product = await product_service.get_product(
            tenant=ctx,
            product_id=product_id
        )
        if not product:
            return json.dumps({"error": "Product not found"})
        return json.dumps(product.model_dump())
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
async def get_collections() -> str:
    """
    Get all product collections available for the current tenant.
    """
    ctx = get_mcp_tenant_context()
    container = get_container()
    # Assuming catalog service or product service handles collections
    # For now, let's pull from typesense facets if there isn't a direct DB call
    typesense = container.get("typesense")
    if not typesense:
        return json.dumps({"error": "Typesense not available"})
        
    try:
        results = await typesense.search(
            collection=ctx.collection_name,
            query="*",
            query_by="title",
            facet_by="collection",
            limit=0
        )
        facets = results.get("facet_counts", [])
        if facets:
            collections = [f["value"] for f in facets[0].get("counts", [])]
            return json.dumps(collections)
        return json.dumps([])
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
async def get_categories() -> str:
    """
    Get all product categories available for the current tenant.
    """
    ctx = get_mcp_tenant_context()
    container = get_container()
    typesense = container.get("typesense")
    if not typesense:
        return json.dumps({"error": "Typesense not available"})
        
    try:
        results = await typesense.search(
            collection=ctx.collection_name,
            query="*",
            query_by="title",
            facet_by="category",
            limit=0
        )
        facets = results.get("facet_counts", [])
        if facets:
            categories = [f["value"] for f in facets[0].get("counts", [])]
            return json.dumps(categories)
        return json.dumps([])
    except Exception as e:
        return json.dumps({"error": str(e)})
