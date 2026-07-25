"""
Legacy Search Endpoints
Maintains compatibility with /api/v1/search/... endpoints
"""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from app.api.dependencies import (
    TenantContext,
    get_container_dependency,
    get_tenant_context,
    require_auth,
    require_same_tenant,
)
from app.models.requests import ChatCompletionMessage, ChatCompletionRequest, SearchRequest
from app.models.responses import SearchResult

router = APIRouter()

@router.get("/config")
async def get_search_config(
    tenant: TenantContext = Depends(get_tenant_context)
):
    """Get public tenant configuration for the widget"""
    return {
        "success": True,
        "config": {
            "primary_color": tenant.config.get("primary_color", "#4f46e5") if tenant.config else "#4f46e5",
            "font_family": tenant.config.get("font_family", "system-ui, -apple-system, sans-serif") if tenant.config else "system-ui, -apple-system, sans-serif",
            "mode": tenant.config.get("mode", "full") if tenant.config else "full" # Defaulting to full for the demo
        }
    }

class PublicChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

@router.post("/chat")
async def public_chat(
    request: PublicChatRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    container = Depends(get_container_dependency)
):
    """Public AI shopping assistant chat"""
    try:
        chat_orchestrator = container.get('chat_orchestrator')
        if not chat_orchestrator:
            raise HTTPException(status_code=503, detail="Chat unavailable")

        chat_req = ChatCompletionRequest(
            messages=[ChatCompletionMessage(role="user", content=request.message)],
            user_id=request.session_id or "anonymous_shopper"
        )

        result = await chat_orchestrator.handle_completion(chat_req, tenant)

        if not result.get('success'):
            raise HTTPException(status_code=500, detail="Chat failed")

        return {"success": True, "answer": result.get("response", "")}
    except Exception:
        return {"success": False, "answer": "I'm sorry, I cannot process your request right now."}

@router.post("", response_model=SearchResult, deprecated=True)
@router.post("/", response_model=SearchResult, include_in_schema=False)
async def search_products(
    request: SearchRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    tenant: TenantContext = Depends(get_tenant_context),
    container = Depends(get_container_dependency)
):
    """Search products (legacy endpoint mapping to products/search)"""
    try:
        search_orchestrator = container.get('search_orchestrator')
        if not search_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search service not available"
            )

        # 4. Query Complexity Limit
        if request.query and len(request.query) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query too long. Max 100 characters."
            )

        user_id = request.user_context.user_id if request.user_context else request.id if hasattr(request, "id") else request.user_id

        result = await search_orchestrator.handle(
            query=request.query,
            user_id=user_id,
            filters=request.filters.model_dump() if request.filters else {},
            limit=request.pagination.limit if request.pagination else 20,
            offset=(request.pagination.page - 1) * request.pagination.limit if request.pagination else 0,
            sort=request.sort.model_dump() if request.sort else None,
            search_type=request.search_type,
            include_suggestions=request.include.suggestions if request.include else False,
            tenant_context=tenant
        )

        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Search failed"
            )

        # Generate unique search ID for telemetry
        import uuid
        search_id = str(uuid.uuid4())

        # Add search_id to result metadata
        meta = result.get("meta", {})
        meta["search_id"] = search_id

        # Record usage event and telemetry in background
        tenant_service = container.get('tenant_service')
        if tenant_service:
            background_tasks.add_task(
                tenant_service.record_usage,
                org_id=tenant.organization_id,
                event_type="search_query",
                query_text=request.query,
                latency_ms=meta.get("latency_ms", 0),
                result_count=result.get("total_results", 0),
                api_key_id=getattr(tenant, "key_id", None)
            )

        cache = container.get('redis')
        if cache:
            telemetry_key = f"telemetry:{tenant.organization_id}:trending_searches:7d"
            background_tasks.add_task(
                cache.zincrby,
                key=telemetry_key,
                amount=1.0,
                member=request.query.lower().strip()
            )
            
            # --- Activation Metric (Live Deployment Tracking) ---
            origin = http_request.headers.get("origin", "")
            if origin and not any(local in origin for local in ["localhost", "127.0.0.1", "0.0.0.0"]):
                activation_key = f"tenant:{tenant.organization_id}:live_searches"
                background_tasks.add_task(cache.incr, activation_key)

        return SearchResult(
            query=request.query,
            results=result.get("results", []),
            total_results=result.get("total_results", 0),
            facets=result.get("facets"),
            meta=meta,
            search_metadata={
                "search_type": request.search_type,
                "suggestions": result.get("suggestions", []) if request.include and request.include.suggestions else None
            }
        )
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed due to an internal server error"
        )


@router.get("/autocomplete")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    limit: int = Query(default=10, ge=1, le=20, description="Number of suggestions"),
    tenant: TenantContext = Depends(get_tenant_context),
    container = Depends(get_container_dependency)
):
    """Get autocomplete suggestions (legacy endpoint mapping to products/search/suggestions)"""
    try:
        search_orchestrator = container.get('search_orchestrator')
        if not search_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search service not available"
            )

        result = await search_orchestrator.get_suggestions(
            query=q,
            limit=limit,
            tenant_context=tenant
        )

        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get suggestions"
            )

        return {
            "query": q,
            "suggestions": result.get("suggestions", []),
            "total": len(result.get("suggestions", []))
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get suggestions due to an internal server error"
        )


@router.get("/trending")
async def get_trending_searches(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(default=10, ge=1, le=20, description="Number of trending searches"),
    tenant: TenantContext = Depends(get_tenant_context),
    container = Depends(get_container_dependency)
):
    """Get trending searches"""
    try:
        search_orchestrator = container.get('search_orchestrator')
        if not search_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search service not available"
            )

        result = await search_orchestrator.get_trending_searches(
            limit=limit,
            category=category,
            tenant_context=tenant
        )

        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get trending searches"
            )

        return {
            "trending_searches": result.get("searches", []),
            "total": len(result.get("searches", [])),
            "category": category
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get trending searches: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get trending searches due to an internal server error"
        )


@router.get("/popular")
async def get_popular_searches(
    limit: int = Query(default=10, ge=1, le=20, description="Number of popular searches"),
    tenant: TenantContext = Depends(get_tenant_context),
    container = Depends(get_container_dependency)
):
    """Get popular searches"""
    try:
        search_orchestrator = container.get('search_orchestrator')
        if not search_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search service not available"
            )

        result = await search_orchestrator.get_trending_searches(
            limit=limit,
            tenant_context=tenant
        )

        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get popular searches"
            )

        return {
            "popular_searches": result.get("searches", []),
            "total": len(result.get("searches", []))
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get popular searches: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get popular searches due to an internal server error"
        )


@router.post("/image")
async def search_by_image_legacy(
    payload: Dict[str, Any],
    container = Depends(get_container_dependency),
    tenant: TenantContext = Depends(get_tenant_context),
    current_user = Depends(require_auth),
):
    """Search products by image (legacy)"""
    try:
        image_orchestrator = container.get('image_orchestrator')
        if not image_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Image search service not available"
            )

        require_same_tenant(current_user, tenant)
        result = await image_orchestrator.search_by_image(
            image_id=payload.get("image_id"),
            image_data=payload.get("image_data"),
            organization_id=tenant.organization_id,
            user_id=current_user["user_id"],
            tenant_context=tenant,
            search_type=payload.get("search_type", "similar"),
            limit=payload.get("limit", 10)
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Image search failed")
            )

        return {
            "success": True,
            "results": result.get("results", []),
            "search_type": payload.get("search_type", "similar"),
            "total": len(result.get("results", [])),
            "image_analysis": result.get("image_analysis")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image search failed due to an internal server error"
        )
