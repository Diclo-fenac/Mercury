"""
Search Endpoints
Product search functionality with various search types
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.models.requests import SearchRequest
from app.models.responses import SearchResult
from app.api.dependencies import get_container_dependency

router = APIRouter()

@router.post("/", response_model=SearchResult)
async def search_products(
    request: SearchRequest,
    container = Depends(get_container_dependency)
):
    """Search products via search orchestrator"""
    try:
        search_orchestrator = container.get('search_orchestrator')
        if not search_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search service not available"
            )
        
        result = await search_orchestrator.handle(
            query=request.query,
            user_id=request.user_id,
            filters=request.filters,
            limit=request.limit
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
            filters_applied=request.filters
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

@router.get("/suggestions")
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
async def get_trending_searches(
    limit: int = Query(default=10, ge=1, le=50, description="Number of trending searches"),
    category: str = Query(None, description="Filter by category"),
    container = Depends(get_container_dependency)
):
    """Get trending searches via search orchestrator"""
    try:
        search_orchestrator = container.get('search_orchestrator')
        if not search_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search service not available"
            )
        
        result = await search_orchestrator.get_trending_searches(
            limit=limit,
            category=category
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get trending searches"
            )
        
        return {
            "trending_searches": result.get("searches", []),
            "category": category,
            "total": len(result.get("searches", []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trending searches: {str(e)}"
        )