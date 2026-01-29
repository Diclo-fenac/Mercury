"""
Product Endpoints
Product information, recommendations, and related operations
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import Optional

from app.models.requests import ProductRecommendationRequest
from app.models.responses import BaseResponse
from app.api.dependencies import get_container_dependency

router = APIRouter()

@router.get("/trending")
async def get_trending_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(default=20, ge=1, le=50, description="Number of products"),
    days: int = Query(default=7, ge=1, le=30, description="Trending period in days"),
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
            limit=limit,
            days=days
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get trending products"
            )
        
        return {
            "trending_products": result.get("products", []),
            "category": category,
            "period_days": days,
            "total": len(result.get("products", [])),
            "trending_criteria": result.get("criteria")
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
    limit: int = Query(default=20, ge=1, le=50, description="Number of deals"),
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
            limit=limit
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get deals"
            )
        
        return {
            "deals": result.get("deals", []),
            "category": category,
            "min_discount": min_discount,
            "total": len(result.get("deals", [])),
            "average_discount": result.get("average_discount", 0)
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
    limit: int = Query(default=10, ge=1, le=50, description="Number of flash deals"),
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
        
        result = await product_orchestrator.get_flash_deals(limit)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get flash deals"
            )
        
        return {
            "flash_deals": result.get("deals", []),
            "total": len(result.get("deals", [])),
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

@router.post("/{product_id}/recommendations")
async def get_product_recommendations(
    request: ProductRecommendationRequest,
    product_id: str = Path(..., description="Product identifier"),
    container = Depends(get_container_dependency)
):
    """Get product recommendations via recommendation orchestrator"""
    try:
        recommendation_orchestrator = container.get('recommendation_orchestrator')
        if not recommendation_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Recommendation service not available"
            )
        
        result = await recommendation_orchestrator.get_product_recommendations(
            product_id=product_id,
            user_id=request.user_id,
            recommendation_type=request.recommendation_type,
            limit=request.limit
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
        
        return {
            "product_id": product_id,
            "recommendations": result.get("recommendations", []),
            "recommendation_type": request.recommendation_type,
            "total": len(result.get("recommendations", []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )