"""
Image Endpoints
Image upload, analysis, and search functionality
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status

from app.api.dependencies import get_container_dependency, require_auth
from app.models.requests import ImageSearchRequest, ImageUploadRequest
from app.models.responses import ImageUploadResponse

router = APIRouter()

@router.post("/", response_model=ImageUploadResponse)
async def upload_image(
    request: ImageUploadRequest,
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Upload and analyze image via image orchestrator (max 5MB, JPEG/PNG/WEBP)"""
    try:
        image_orchestrator = container.get('image_orchestrator')
        if not image_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Image service not available"
            )

        result = await image_orchestrator.process_image_upload(
            image_data=request.image_data,
            user_id=current_user["user_id"],
            message=request.message
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Image upload failed")
            )

        # Map the complex processor analysis to the API ImageAnalysis response model
        processor_analysis = result.get("analysis", {})
        if "description" in processor_analysis:
            mapped_analysis = processor_analysis
        else:
            barcode_info = processor_analysis.get("barcode_detection", {}) or {}
            product_info = processor_analysis.get("product_identification", {}) or {}
            mapped_analysis = {
                "description": product_info.get("description") or "Product image",
                "is_barcode": barcode_info.get("is_barcode", False),
                "barcode_data": barcode_info.get("barcode_data"),
                "barcode_type": barcode_info.get("barcode_type"),
                "confidence_score": product_info.get("confidence") or barcode_info.get("confidence") or 1.0
            }

        return ImageUploadResponse(
            image_id=result.get("image_id", ""),
            image_url=result.get("image_url", ""),
            analysis=mapped_analysis
        )


    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image upload failed: {str(e)}"
        )

@router.get("/{image_id}")
async def get_image_details(
    image_id: str = Path(..., description="Image identifier"),
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Get image metadata and analysis results"""
    try:
        image_orchestrator = container.get('image_orchestrator')
        if not image_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Image service not available"
            )

        result = await image_orchestrator.get_image_metadata(
            image_id=image_id,
            user_id=current_user["user_id"]
        )

        if not result.get("success"):
            if result.get("error") == "not_found":
                raise HTTPException(status_code=404, detail="Image not found")
            elif result.get("error") == "access_denied":
                raise HTTPException(status_code=403, detail="Access denied")
            else:
                raise HTTPException(status_code=500, detail=result.get("error"))

        return result.get("image")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get image details: {str(e)}"
        )

@router.post("/search")
async def search_by_image(
    request: ImageSearchRequest,
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Search products by image via image orchestrator"""
    try:
        image_orchestrator = container.get('image_orchestrator')
        if not image_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Image search service not available"
            )

        result = await image_orchestrator.search_by_image(
            image_id=request.image_id,
            image_data=request.image_data,
            user_id=current_user["user_id"],
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

@router.get("/{image_id}/analysis", deprecated=True)
async def get_image_analysis(
    image_id: str = Path(..., description="Image identifier"),
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Get cached image analysis results (legacy)"""
    try:
        image_orchestrator = container.get('image_orchestrator')
        if not image_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Image service not available"
            )

        result = await image_orchestrator.get_image_metadata(
            image_id=image_id,
            user_id=current_user["user_id"]
        )

        if not result.get("success"):
            if result.get("error") == "not_found":
                raise HTTPException(status_code=404, detail="Image not found")
            elif result.get("error") == "access_denied":
                raise HTTPException(status_code=403, detail="Access denied")
            else:
                raise HTTPException(status_code=500, detail=result.get("error"))

        image_data = result.get("image", {})
        return {
            "image_id": image_id,
            "analysis": image_data.get("analysis", {})
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get image analysis: {str(e)}"
        )

import os
from pathlib import Path as FilePath

from fastapi.responses import FileResponse


@router.get("/{image_id}/raw")
async def get_raw_image(
    image_id: str = Path(..., description="Image identifier"),
    container = Depends(get_container_dependency)
):
    """Serve the raw uploaded image file from storage (MinIO or local disk)"""
    # Sanitize to prevent directory traversal
    safe_image_id = os.path.basename(image_id)
    if not safe_image_id.endswith(".jpg"):
        filename = f"{safe_image_id}.jpg"
    else:
        filename = safe_image_id
        
    storage = container.get('storage')
    if not storage:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Storage service not available")
        
    # Optimisation for LocalStorageClient to serve directly from file
    from app.infrastructure.storage.local import LocalStorageClient
    if isinstance(storage, LocalStorageClient):
        uploads_dir = FilePath("uploads")
        filepath = uploads_dir / filename
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Image file not found")
        return FileResponse(filepath, media_type="image/jpeg")
        
    # Retrieve bytes from MinIO/S3 and stream them
    try:
        data = await storage.download_blob(filename)
        if not data:
            raise HTTPException(status_code=404, detail="Image not found in storage")
        return Response(content=data, media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve image: {str(e)}"
        )