"""
Widget Endpoints - Layer 6: API
Supports instant search suggestions and widget config retrieval using public search keys.
"""
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import TenantContext, get_container_dependency, get_tenant_context

router = APIRouter()


@router.get("/config")
async def get_widget_config(
    tenant_ctx: TenantContext = Depends(get_tenant_context)
):
    """
    Get public styling and branding configuration for the widget.
    Allows public keys.
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
    q: str = Query(..., min_length=1, description="Query string"),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    container = Depends(get_container_dependency)
):
    """
    Ultra-fast keyword-only search for typeahead. Target latency < 30ms.
    """
    typesense_client = container.get("typesense")
    if not typesense_client or not typesense_client._connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search engine not available"
        )

    collection_name = f"tenant_{tenant_ctx.organization_id}_products"
    
    try:
        # Fast query search
        loop = typesense_client.client.collections[collection_name].documents.search
        res = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: loop({
                "q": q,
                "query_by": "title,brand,category",
                "per_page": 5,
                "prefix": True,
                "typo_tokens_threshold": 1,
                "num_typos": 1
            })
        )
        
        suggestions = []
        hits = res.get("hits", [])
        for hit in hits:
            doc = hit.get("document", {})
            suggestions.append({
                "id": doc.get("id"),
                "title": doc.get("title") or doc.get("name"),
                "brand": doc.get("brand"),
                "category": doc.get("category"),
                "price": doc.get("selling_price"),
                "in_stock": doc.get("stock")
            })
            
        return {
            "success": True,
            "suggestions": suggestions
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Instant search failed: {str(e)}"
        )


from typing import Optional

from pydantic import BaseModel, Field


class WidgetChatRequest(BaseModel):
    query: str = Field(..., description="The user's question or search query")
    conversation_id: Optional[str] = Field(None, description="Optional conversation session ID")


@router.post("/chat")
async def widget_chat(
    request: WidgetChatRequest,
    tenant_ctx: TenantContext = Depends(get_tenant_context),
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
        
        # 2. Format products for LLM context
        products_context = ""
        for p in products:
            desc = p.get("description", "")
            if len(desc) > 120:
                desc = desc[:120] + "..."
            products_context += (
                f"- ID: {p.get('id')}\n"
                f"  Title: {p.get('title')}\n"
                f"  Brand: {p.get('brand')}\n"
                f"  Price: ${p.get('selling_price')}\n"
                f"  Description: {desc}\n"
                f"  Stock: {'In Stock' if p.get('stock') else 'Out of Stock'}\n\n"
            )
            
        # 3. Generate response using LLM
        prompt = (
            f"You are a helpful shopping assistant for '{tenant_ctx.organization_slug}'. "
            "Help the user find products from the list below and answer their question. "
            "Keep the response brief, professional, and conversational. Refer to the products provided.\n\n"
            f"Relevant Products:\n{products_context if products_context else 'No products found matching the query.'}\n"
            f"User Query: {sanitized_query}\n"
            "Assistant Response:"
        )
        
        answer = await llm_engine.generate(prompt)
        
        return {
            "success": True,
            "response": answer or "I'm sorry, I couldn't generate a response. How else can I help you?",
            "products": products,
            "conversation_id": request.conversation_id or "session_" + tenant_ctx.organization_id[:8]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Widget chat failed: {str(e)}"
        )
