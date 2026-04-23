"""
Product Endpoints
Product information, recommendations, and related operations
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.api.dependencies import PaginationParams, get_container_dependency
from app.models.requests import SearchRequest
from app.models.responses import SearchResult

router = APIRouter()

@router.post("/search", response_model=SearchResult)
async def search_products(
    request: SearchRequest,
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
        
        # Extract user_id from context or top level
        user_id = request.user_context.user_id if request.user_context else request.user_id
        
        result = await search_orchestrator.handle(
            query=request.query,
            user_id=user_id,
            filters=request.filters.dict() if request.filters else {},
            limit=request.pagination.limit if request.pagination else 20,
            offset=(request.pagination.page - 1) * request.pagination.limit if request.pagination else 0,
            sort=request.sort.dict() if request.sort else None,
            search_type=request.search_type,
            include_suggestions=request.include.suggestions if request.include else False
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Search failed"
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
            limit=limit
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

@router.get("/trending")
async def get_trending_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    days: int = Query(default=7, ge=1, le=30, description="Trending period in days"),
    pagination: PaginationParams = Depends(),
    container = Depends(get_container_dependency)
):
    """Get trending products via product orchestrator"""
    try:
        product_orchestrator = container.get('product_orchestrator')
        if not product_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Product service not available"
            )
        
        result = await product_orchestrator.get_trending_products(
            category=category,
            limit=pagination.limit,
            days=days
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get trending products"
            )
        
        products = result.get("products", [])
        total = len(products) # In real app, get total from DB
        
        return {
            "trending_products": products,
            "category": category,
            "period_days": days,
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
            detail=f"Failed to get trending products: {str(e)}"
        )

@router.get("/deals")
async def get_deals(
    category: Optional[str] = Query(None, description="Filter by category"),
    min_discount: float = Query(default=20.0, ge=0, le=100, description="Minimum discount percentage"),
    pagination: PaginationParams = Depends(),
    container = Depends(get_container_dependency)
):
    """Get product deals via product orchestrator"""
    try:
        product_orchestrator = container.get('product_orchestrator')
        if not product_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Product service not available"
            )
        
        result = await product_orchestrator.get_deals(
            category=category,
            min_discount=min_discount,
            limit=pagination.limit
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get deals"
            )
        
        deals = result.get("deals", [])
        total = len(deals)
        
        return {
            "deals": deals,
            "category": category,
            "min_discount": min_discount,
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
            detail=f"Failed to get deals: {str(e)}"
        )

@router.get("/flash-deals")
async def get_flash_deals(
    pagination: PaginationParams = Depends(),
    container = Depends(get_container_dependency)
):
    """Get flash deals via product orchestrator"""
    try:
        product_orchestrator = container.get('product_orchestrator')
        if not product_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Product service not available"
            )
        
        result = await product_orchestrator.get_flash_deals(pagination.limit)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get flash deals"
            )
        
        deals = result.get("deals", [])
        total = len(deals)
        
        return {
            "flash_deals": deals,
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.limit,
                "total": total,
                "pages": (total + pagination.limit - 1) // pagination.limit if pagination.limit > 0 else 1
            },
            "expires_soon": result.get("expires_soon", True)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flash deals: {str(e)}"
        )

@router.get("/{product_id}")
async def get_product(
    product_id: str = Path(..., description="Product identifier"),
    user_id: Optional[str] = Query(None, description="User identifier for activity tracking"),
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
            user_id=user_id
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
    container = Depends(get_container_dependency)
):
    """Get product recommendations via recommendation orchestrator"""
    try:
        # Validate recommendation type
        allowed_types = ['similar', 'complementary', 'substitute', 'variant']
        if recommendation_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
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
            limit=pagination.limit
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
