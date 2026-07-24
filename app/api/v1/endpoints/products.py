"""
Product Endpoints
Product information, recommendations, and related operations
"""
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, Query, status

from app.api.dependencies import (
    PaginationParams,
    TenantContext,
    get_container_dependency,
    get_tenant_context,
)
from app.models.requests import SearchRequest
from app.models.responses import SearchResult

router = APIRouter()

@router.post("/search", response_model=SearchResult)
async def search_products(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    tenant: TenantContext = Depends(get_tenant_context),
    container = Depends(get_container_dependency)
):
    """Search products via search orchestrator with advanced filters and hybrid retrieval"""
    try:
        search_orchestrator = container.get('search_orchestrator')
        if not search_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search service not available"
            )
        
        user_id = request.user_context.user_id if request.user_context else request.user_id
        
        result = await search_orchestrator.handle(
            query=request.query,
            user_id=user_id,
            filters=request.filters.dict() if request.filters else {},
            limit=request.pagination.limit if request.pagination else 20,
            offset=(request.pagination.page - 1) * request.pagination.limit if request.pagination else 0,
            sort=request.sort.dict() if request.sort else None,
            search_type=request.search_type,
            include_suggestions=request.include.suggestions if request.include else False,
            tenant_context=tenant
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Search failed"
            )
        
        # Record usage event in background
        tenant_service = container.get('tenant_service')
        if tenant_service:
            background_tasks.add_task(
                tenant_service.record_usage,
                org_id=tenant.organization_id,
                event_type="search_query",
                query_text=request.query,
                latency_ms=result.get("meta", {}).get("latency_ms", 0),
                result_count=result.get("total_results", 0),
                api_key_id=getattr(tenant, "key_id", None)
            )

        return SearchResult(
            query=request.query,
            results=result.get("results", []),
            total_results=result.get("total_results", 0),
            facets=result.get("facets"),
            meta=result.get("meta"),
            search_metadata={
                "search_type": request.search_type,
                "suggestions": result.get("suggestions", []) if request.include and request.include.suggestions else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@router.get("/search/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    limit: int = Query(default=10, ge=1, le=20, description="Number of suggestions"),
    tenant: TenantContext = Depends(get_tenant_context),
    container = Depends(get_container_dependency)
):
    """Get search suggestions via search orchestrator"""
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        )


@router.get("/{product_id}")
async def get_product(
    product_id: str = Path(..., description="Product identifier"),
    user_id: Optional[str] = Query(None, description="User identifier for activity tracking"),
    tenant: TenantContext = Depends(get_tenant_context),
    container = Depends(get_container_dependency)
):
    """Get detailed product information via product orchestrator"""
    try:
        product_orchestrator = container.get('product_orchestrator')
        if not product_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Product service not available"
            )
        
        result = await product_orchestrator.get_product_details(
            product_id=product_id,
            user_id=user_id,
            organization_id=tenant.organization_id,
        )
        
        if not result.get('success'):
            if result.get('error') == 'not_found':
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get product"
                )
        
        return result.get("product")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get product: {str(e)}"
        )

@router.get("/{product_id}/recommendations")
async def get_product_recommendations(
    product_id: str = Path(..., description="Product identifier"),
    user_id: Optional[str] = Query(None, description="User identifier"),
    recommendation_type: str = Query(default="similar", description="Recommendation type: similar, complementary, substitute, variant"),
    pagination: PaginationParams = Depends(),
    tenant: TenantContext = Depends(get_tenant_context),
    container = Depends(get_container_dependency)
):
    """Get product recommendations via recommendation orchestrator"""
    try:
        # Validate recommendation type
        allowed_types = ['similar', 'complementary', 'substitute', 'variant']
        if recommendation_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"recommendation_type must be one of {allowed_types}"
            )

        recommendation_orchestrator = container.get('recommendation_orchestrator')
        if not recommendation_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Recommendation service not available"
            )
        
        result = await recommendation_orchestrator.get_product_recommendations(
            product_id=product_id,
            user_id=user_id,
            recommendation_type=recommendation_type,
            limit=pagination.limit,
            organization_id=tenant.organization_id,
        )
        
        if not result.get('success'):
            if result.get('error') == 'not_found':
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get recommendations"
                )
        
        recommendations = result.get("recommendations", [])
        total = len(recommendations)
        
        return {
            "product_id": product_id,
            "recommendations": recommendations,
            "recommendation_type": recommendation_type,
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.limit,
                "total": total,
                "pages": (total + pagination.limit - 1) // pagination.limit if pagination.limit > 0 else 1
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )
