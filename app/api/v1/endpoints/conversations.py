"""
Conversation Endpoints
Conversation management and history
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path

from app.models.requests import ConversationCreate
from app.models.responses import ConversationListResponse, ConversationDetailResponse
from app.api.dependencies import get_container_dependency, require_auth

router = APIRouter()

@router.get("/{user_id}", response_model=ConversationListResponse)
async def get_user_conversations(
    user_id: str = Path(..., description="User identifier"),
    limit: int = Query(default=20, ge=1, le=100, description="Number of conversations"),
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Get all conversations for authenticated user"""
    try:
        # Verify user can only access their own conversations
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
        
        result = await conversation_orchestrator.get_user_conversations(
            user_id=user_id,
            limit=limit
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get conversations"
            )
        
        return ConversationListResponse(
            conversations=result.get("conversations", []),
            total=result.get("total", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversations: {str(e)}"
        )

@router.get("/{user_id}/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation_details(
    user_id: str = Path(..., description="User identifier"),
    conversation_id: str = Path(..., description="Conversation identifier"),
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Get detailed conversation information"""
    try:
        # Verify user can only access their own conversations
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
        
        result = await conversation_orchestrator.get_conversation_details(
            user_id=user_id,
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

@router.post("/{user_id}")
async def create_conversation(
    request: ConversationCreate,
    user_id: str = Path(..., description="User identifier"),
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Create new conversation for authenticated user"""
    try:
        # Verify user can only create conversations for themselves
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

@router.delete("/{user_id}/{conversation_id}")
async def delete_conversation(
    user_id: str = Path(..., description="User identifier"),
    conversation_id: str = Path(..., description="Conversation identifier"),
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Delete conversation for authenticated user"""
    try:
        # Verify user can only delete their own conversations
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
        
        result = await conversation_orchestrator.delete_conversation(
            user_id=user_id,
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