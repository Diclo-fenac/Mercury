"""
Widget Endpoints - Layer 6: API
Supports instant search suggestions and widget config retrieval using public search keys.

SECURITY: All endpoints in this router REQUIRE a public (pk_*) key.
Admin (sk_*) keys are explicitly rejected.
"""
import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

logger = logging.getLogger(__name__)

from app.api.dependencies import TenantContext, get_container_dependency, get_tenant_context

router = APIRouter()


async def require_public_key(
    tenant_ctx: TenantContext = Depends(get_tenant_context),
) -> TenantContext:
    """Reject admin/private keys on all public widget endpoints."""
    if tenant_ctx.key_type != "public_search":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public search key (pk_*) required for widget endpoints",
        )
    return tenant_ctx


@router.get("/config")
async def get_widget_config(
    tenant_ctx: TenantContext = Depends(require_public_key)
):
    """
    Get public styling and branding configuration for the widget.
    Requires a public (pk_*) key.
    """
    config = tenant_ctx.config or {}
    return {
        "success": True,
        "config": {
            "widget_primary_color": config.get("widget_primary_color", "#6366f1"),
            "widget_font_family": config.get("widget_font_family", "Inter"),
            "widget_position": config.get("widget_position", "center"),
            "widget_placeholder": config.get("widget_placeholder", "Search products..."),
            "out_of_stock_behavior": config.get("out_of_stock_behavior", "demote")
        }
    }


@router.get("/search/instant")
async def instant_search(
    q: str = Query(..., min_length=1, max_length=100, description="Query string"),
    limit: int = Query(default=8, ge=1, le=50, description="Max results"),
    tenant_ctx: TenantContext = Depends(require_public_key),
    container = Depends(get_container_dependency)
):
    """
    Ultra-fast keyword-only search for typeahead. Target latency < 30ms.
    Requires a public (pk_*) key. Admin keys are rejected.
    """
    typesense_client = container.get("typesense")
    if not typesense_client or not typesense_client._connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search engine not available"
        )

    collection_name = f"tenant_{tenant_ctx.organization_id}_products"
    search_id = str(uuid.uuid4())

    try:
        loop = typesense_client.client.collections[collection_name].documents.search
        res = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: loop({
                "q": q,
                "query_by": "title,brand,category",
                "per_page": limit,
                "prefix": True,
                "typo_tokens_threshold": 1,
                "num_typos": 1
            })
        )

        suggestions = []
        hits = res.get("hits", [])
        for hit in hits:
            doc = hit.get("document", {})
            # Return only safe, storefront-facing fields — no internal IDs or credentials
            suggestions.append({
                "id": doc.get("id"),
                "title": doc.get("title") or doc.get("name"),
                "brand": doc.get("brand"),
                "category": doc.get("category"),
                "price": doc.get("selling_price"),
                "in_stock": doc.get("stock"),
                "image_url": doc.get("image_url") or "",
                "url": doc.get("url") or doc.get("product_url") or "",
            })

        return {
            "success": True,
            "search_id": search_id,  # For telemetry click attribution
            "suggestions": suggestions
        }
    except Exception as e:
        logger.error(f"Instant search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Instant search failed due to an internal server error"
        )


from typing import Optional

from pydantic import BaseModel, Field


class WidgetChatRequest(BaseModel):
    query: str = Field(..., description="The user's question or search query")
    conversation_id: Optional[str] = Field(None, description="Optional conversation session ID")


@router.post("/chat")
async def widget_chat(
    request: WidgetChatRequest,
    tenant_ctx: TenantContext = Depends(require_public_key),
    container = Depends(get_container_dependency)
):
    """
    RAG-powered chat assistant for the merchant widget. Returns a text answer and matching product cards.
    """
    search_orchestrator = container.get("search_orchestrator")
    llm_engine = container.get("llm_engine")
    if not search_orchestrator or not llm_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat indexing services not available"
        )

    try:
        from app.core.security.input_sanitizer import sanitize_user_input
        sanitized_query, is_suspicious = sanitize_user_input(request.query)
        if is_suspicious:
            return {
                "success": True,
                "response": sanitized_query,
                "products": [],
                "conversation_id": request.conversation_id or "session_" + tenant_ctx.organization_id[:8]
            }

        # 1. Fetch matching products using the tenant search pipeline (applies pins, synonyms, stock beh)
        search_res = await search_orchestrator.handle(
            query=sanitized_query,
            user_id=request.conversation_id or "anonymous",
            filters={},
            limit=5,
            tenant_context=tenant_ctx
        )

        products = search_res.get("results", [])

        # Grounded engine always re-runs tenant-scoped retrieval and returns only
        # verified catalog citations. Never send untrusted catalog text as a prompt.
        from app.core.security.context import tenant_context_var, user_id_var

        tenant_context_var.set(tenant_ctx)
        user_id_var.set(request.conversation_id or "anonymous")
        answer = await llm_engine.generate_with_tools(sanitized_query, tenant_context=tenant_ctx)
        if not answer.get("success"):
            raise HTTPException(status_code=503, detail="Catalog assistant unavailable")

        return {
            "success": True,
            "response": answer["response"],
            "products": products,
            "citations": answer.get("citations", []),
            "conversation_id": request.conversation_id or "session_" + tenant_ctx.organization_id[:8]
        }
    except Exception as e:
        logger.error(f"Widget chat failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Widget chat failed due to an internal server error"
        )
