"""
Image Endpoints
Image upload, analysis, and search functionality
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.requests import ImageUploadRequest, ImageSearchRequest
from app.models.responses import ImageUploadResponse
from app.api.dependencies import get_container_dependency, require_auth

router = APIRouter()

@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(
    request: ImageUploadRequest,
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Upload and analyze image via image orchestrator"""
    try:
        # Verify user can only upload for themselves
        if current_user["user_id"] != request.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        image_orchestrator = container.get('image_orchestrator')
        if not image_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Image service not available"
            )
        
        result = await image_orchestrator.process_image_upload(
            image_data=request.image_data,
            user_id=request.user_id,
            message=request.message
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Image upload failed")
            )
        
        return ImageUploadResponse(
            image_id=result.get("image_id", ""),
            image_url=result.get("image_url", ""),
            analysis=result.get("analysis", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image upload failed: {str(e)}"
        )

@router.post("/search")
async def search_by_image(
    request: ImageSearchRequest,
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Search products by image via search orchestrator"""
    try:
        # Verify user can only search for themselves
        if current_user["user_id"] != request.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        search_orchestrator = container.get('search_orchestrator')
        if not search_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search service not available"
            )
        
        result = await search_orchestrator.search_by_image(
            image_id=request.image_id,
            image_data=request.image_data,
            user_id=request.user_id,
            search_type=request.search_type,
            limit=request.limit
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Image search failed")
            )
        
        return {
            "success": True,
            "results": result.get("results", []),
            "search_type": request.search_type,
            "total": len(result.get("results", [])),
            "image_analysis": result.get("image_analysis")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image search failed: {str(e)}"
        )