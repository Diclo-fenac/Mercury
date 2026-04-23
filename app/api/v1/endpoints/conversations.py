"""
Conversation Endpoints
Conversation management and history
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.api.dependencies import PaginationParams, get_container_dependency, require_auth
from app.models.requests import ConversationCreate
from app.models.responses import ConversationDetailResponse, ConversationListResponse

router = APIRouter()

@router.get("/", response_model=ConversationListResponse)
async def get_user_conversations(
    user_id: Optional[str] = Query(None, description="User identifier (defaults to current user)"),
    pagination: PaginationParams = Depends(),
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Get all conversations for authenticated user"""
    try:
        # Resolve user_id: use provided or default to current user
        target_user_id = user_id or current_user["user_id"]
        
        # Verify authorization: users can currently only access their own data
        if current_user["user_id"] != target_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        conversation_orchestrator = container.get('conversation_orchestrator')
        if not conversation_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Conversation service not available"
            )
        
        result = await conversation_orchestrator.get_user_conversations(
            user_id=target_user_id,
            limit=pagination.limit
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get conversations"
            )
        
        conversations = result.get("conversations", [])
        total = result.get("total", 0)
        
        return ConversationListResponse(
            conversations=conversations,
            total=total,
            pagination={
                "page": pagination.page,
                "per_page": pagination.limit,
                "total": total,
                "pages": (total + pagination.limit - 1) // pagination.limit if pagination.limit > 0 else 1
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversations: {str(e)}"
        )

@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation_details(
    conversation_id: str = Path(..., description="Conversation identifier"),
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Get detailed conversation information"""
    try:
        conversation_orchestrator = container.get('conversation_orchestrator')
        if not conversation_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Conversation service not available"
            )

        # Identity is resolved from token, orchestrator checks ownership
        result = await conversation_orchestrator.get_conversation_details(
            user_id=current_user["user_id"],
            conversation_id=conversation_id
        )

        if not result.get('success'):
            if result.get('error') == 'not_found':
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
            elif result.get('error') == 'access_denied':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get conversation details"
                )

        return ConversationDetailResponse(
            conversation=result.get("conversation")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation: {str(e)}"
        )

@router.post("/")
async def create_conversation(
    request: ConversationCreate,
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Create new conversation for authenticated user"""
    try:
        # User ID is taken from the request (if provided and auth allows) or authenticated token
        user_id = request.user_id or current_user["user_id"]

        if current_user["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        conversation_orchestrator = container.get('conversation_orchestrator')
        if not conversation_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Conversation service not available"
            )

        result = await conversation_orchestrator.create_conversation(
            user_id=user_id,
            title=request.title,
            metadata=request.metadata
        )

        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create conversation"
            )

        return {
            "success": True,
            "conversation_id": result.get("conversation_id"),
            "title": result.get("title"),
            "created_at": result.get("created_at")
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}"
        )

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str = Path(..., description="Conversation identifier"),
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Delete conversation for authenticated user"""
    try:
        conversation_orchestrator = container.get('conversation_orchestrator')
        if not conversation_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Conversation service not available"
            )

        # Identity is resolved from token, orchestrator checks ownership
        result = await conversation_orchestrator.delete_conversation(
            user_id=current_user["user_id"],
            conversation_id=conversation_id
        )

        if not result.get('success'):
            if result.get('error') == 'not_found':
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
            elif result.get('error') == 'access_denied':
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to delete conversation"
                )

        return {"message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )