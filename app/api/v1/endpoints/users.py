"""
User Endpoints
User profile management, preferences, and activity tracking
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.api.dependencies import PaginationParams, get_container_dependency, require_auth, validate_user_id
from app.models.responses import UserProfileResponse

router = APIRouter()

@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: str = Path(..., description="User identifier"),
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Get user profile information for authenticated user"""
    validate_user_id(user_id)
    try:
        # Verify user can only access their own profile
        if current_user["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        user_orchestrator = container.get('user_orchestrator')
        if not user_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="User service not available"
            )
        
        result = await user_orchestrator.get_user_profile(user_id)
        
        if not result.get("success"):
            if result.get('error') == 'not_found':
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User profile not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get user profile"
                )
        
        return UserProfileResponse(
            profile=result.get("profile")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user profile: {str(e)}"
        )


@router.get("/{user_id}/preferences")
async def get_user_preferences(
    user_id: str = Path(..., description="User identifier"),
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Get user preferences for authenticated user"""
    validate_user_id(user_id)
    try:
        # Verify user can only access their own preferences
        if current_user["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        user_orchestrator = container.get('user_orchestrator')
        if not user_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="User service not available"
            )
        
        result = await user_orchestrator.get_user_preferences(user_id)
        
        if not result.get("success"):
            if result.get('error') == 'not_found':
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User preferences not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get user preferences"
                )
        
        return {
            "user_id": user_id,
            "preferences": result.get("preferences", {}),
            "last_updated": result.get("last_updated")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user preferences: {str(e)}"
        )