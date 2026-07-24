import json
from typing import Optional

from app.container import get_container
from app.mcp.context import get_mcp_tenant_context
from app.mcp.server import mcp


@mcp.tool()
async def chat_catalog(message: str, user_id: str, conversation_id: Optional[str] = None) -> str:
    """
    Chat with the catalog AI assistant.
    Provides grounded catalog evidence and citations.
    """
    ctx = get_mcp_tenant_context()
    container = get_container()
    chat_orchestrator = container.get("chat_orchestrator")

    if not chat_orchestrator:
        return json.dumps({"error": "Chat orchestrator not available"})

    try:
        from app.models.requests import ChatRequest
        request = ChatRequest(
            message=message,
            conversation_id=conversation_id
        )

        response = await chat_orchestrator.chat(
            tenant=ctx,
            user_id=user_id,
            request=request
        )
        return json.dumps({
            "message": response.message,
            "conversation_id": response.conversation_id,
            "citations": [c.model_dump() for c in response.citations] if response.citations else []
        })
    except Exception as e:
        return json.dumps({"error": str(e)})
