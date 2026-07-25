"""
Chat Endpoints
Chat functionality with AI assistant
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

from app.api.dependencies import (
    PaginationParams,
    TenantContext,
    get_container_dependency,
    get_tenant_context,
    require_auth,
    require_same_tenant,
)
from app.core.security.context import tenant_context_var, user_id_var
from app.models.requests import ChatCompletionRequest, ChatToolsRequest
from app.models.responses import ChatResponse

router = APIRouter()

@router.post("/completions", response_model=ChatResponse)
async def chat_completion(
    request: ChatCompletionRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """OpenAI-style chat completions (batch mode)"""
    try:
        chat_orchestrator = container.get('chat_orchestrator')
        if not chat_orchestrator or getattr(chat_orchestrator, 'llm', None) is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Chat service not available"
            )

        # Verify user authorization
        user_id = request.user_id or current_user["user_id"]
        if current_user["user_id"] != user_id:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        require_same_tenant(current_user, tenant)

        # Set request-scoped context variables
        tenant_context_var.set(tenant)
        user_id_var.set(user_id)

        # Map new model to orchestrator
        result = await chat_orchestrator.handle_completion(request, tenant, user_id=user_id)

        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Chat processing failed')
            )

        return ChatResponse(
            response=result.get("response", ""),
            conversation_id=request.conversation_id or result.get("conversation_id", "unknown"),
            message_id=result.get("message_id", "unknown"),
            features_used=result.get("features_used", {}),
            citations=result.get("citations", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat failed due to an internal server error"
        )

@router.post("/stream")
async def chat_stream(
    request: ChatCompletionRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Streaming chat completions using Server-Sent Events (SSE)"""
    try:
        chat_orchestrator = container.get('chat_orchestrator')
        if not chat_orchestrator or getattr(chat_orchestrator, 'llm', None) is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Chat service not available"
            )

        user_id = request.user_id or current_user["user_id"]
        if current_user["user_id"] != user_id:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        require_same_tenant(current_user, tenant)

        # Set request-scoped context variables
        tenant_context_var.set(tenant)
        user_id_var.set(user_id)

        return StreamingResponse(
            chat_orchestrator.stream_completion(request, tenant, user_id=user_id),
            media_type="text/event-stream"
        )

    except Exception as e:
        logger.error(f"Streaming failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Streaming failed due to an internal server error"
        )

@router.post("/tools")
async def chat_tools(
    request: ChatToolsRequest,
    tenant: TenantContext = Depends(get_tenant_context),
    container = Depends(get_container_dependency),
    current_user = Depends(require_auth)
):
    """Discover or execute specific tools"""
    try:
        require_same_tenant(current_user, tenant)
        chat_orchestrator = container.get('chat_orchestrator')
        if not chat_orchestrator:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Chat service not available"
            )

        if request.operation == "discover":
            tools = await chat_orchestrator.get_available_tools()
            return {"success": True, "tools": tools}
        else:
            tenant_context_var.set(tenant)
            user_id_var.set(current_user["user_id"])
            result = await chat_orchestrator.execute_tool(
                request.tool_name,
                request.parameters,
                user_id=current_user["user_id"]
            )
            return {"success": True, "result": result}

    except Exception as e:
        logger.error(f"Tool operation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tool operation failed due to an internal server error"
        )

@router.get("/history/{conversation_id}")
async def get_conversation_history(
    conversation_id: str,
    pagination: PaginationParams = Depends(),
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
            organization_id=current_user["organization_id"],
            conversation_id=conversation_id,
            user_id=current_user["user_id"],
            limit=pagination.limit
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

        messages = result.get("messages", [])
        total = len(messages)

        return {
            "success": True,
            "conversation_id": conversation_id,
            "messages": messages,
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
        logger.error(f"Failed to get history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get history due to an internal server error"
        )
