"""
Chat Endpoints
Chat functionality with AI assistant
"""
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.requests import ChatMessage
from app.models.responses import ChatResponse
from app.api.dependencies import get_container_dependency, require_auth

router = APIRouter()

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatMessage,
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Send chat message to AI assistant"""
    try:
        chat_orchestrator = container.get('chat_orchestrator')
        if not chat_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Chat service not available"
            )
        
        # Verify user owns the conversation
        if current_user["user_id"] != request.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        result = await chat_orchestrator.handle(
            message=request.message,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            message_type=request.message_type,
            image_data=request.image_data
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Chat processing failed')
            )
        
        return ChatResponse(
            response=result.get("response", ""),
            conversation_id=request.conversation_id,
            function_called=result.get("function_called"),
            image_analysis=result.get("image_analysis"),
            features_used=result.get("features_used", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )

@router.get("/history/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Get conversation message history"""
    try:
        conversation_orchestrator = container.get('conversation_orchestrator')
        if not conversation_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Conversation service not available"
            )
        
        result = await conversation_orchestrator.get_conversation_history(
            conversation_id=conversation_id,
            user_id=current_user["user_id"],
            limit=50
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
                    detail="Failed to get conversation history"
                )
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "messages": result.get("messages", []),
            "total": len(result.get("messages", []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get history: {str(e)}"
        )