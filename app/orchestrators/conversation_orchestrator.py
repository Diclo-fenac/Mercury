"""
Conversation Orchestrator - Layer 2: Orchestration
Coordinates conversation workflow
"""
from typing import Any, Dict, Optional

from app.domain.conversations.service import ConversationService


class ConversationOrchestrator:
    """Orchestrates conversation workflow"""
    
    def __init__(self, conversation_service: ConversationService):
        self.conversations = conversation_service
    
    async def get_user_conversations(self, user_id: str, limit: int = 20) -> Dict[str, Any]:
        """Get user's conversations"""
        try:
            conversations = await self.conversations.get_user_conversations(user_id, limit)
            return {
                "success": True,
                "conversations": conversations,
                "total": len(conversations)
            }
        except Exception as e:
            raise Exception(f"Failed to get user conversations: {str(e)}")
    
    async def get_conversation_details(self, user_id: str, conversation_id: str) -> Dict[str, Any]:
        """Get conversation details with access control"""
        try:
            conversation = await self.conversations.get_conversation(conversation_id)
            
            if not conversation:
                return {"success": False, "error": "not_found"}
            
            # Check if user owns this conversation
            if conversation.get('user_id') != user_id:
                return {"success": False, "error": "access_denied"}
            
            return {
                "success": True,
                "conversation": conversation
            }
        except Exception as e:
            raise Exception(f"Failed to get conversation details: {str(e)}")
    
    async def create_conversation(self, user_id: str, title: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create new conversation"""
        try:
            conversation_id = await self.conversations.create_conversation(user_id, title)
            conversation = await self.conversations.get_conversation(conversation_id)
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "title": conversation.get('title') if conversation else title,
                "created_at": conversation.get('created_at') if conversation else None
            }
        except Exception as e:
            raise Exception(f"Failed to create conversation: {str(e)}")
    
    async def delete_conversation(self, user_id: str, conversation_id: str) -> Dict[str, Any]:
        """Delete conversation with access control"""
        try:
            conversation = await self.conversations.get_conversation(conversation_id)
            
            if not conversation:
                return {"success": False, "error": "not_found"}
            
            # Check if user owns this conversation
            if conversation.get('user_id') != user_id:
                return {"success": False, "error": "access_denied"}
            
            success = await self.conversations.delete_conversation(conversation_id)
            
            if not success:
                raise Exception("Failed to delete conversation from database")
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "deleted_at": conversation.get('updated_at')
            }
        except Exception as e:
            raise Exception(f"Failed to delete conversation: {str(e)}")
    
    async def get_conversation_history(self, conversation_id: str, user_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get conversation message history with access control"""
        try:
            # Check if user owns this conversation
            conversation = await self.conversations.get_conversation(conversation_id)
            if not conversation:
                return {"success": False, "error": "not_found"}
            
            if conversation.get('user_id') != user_id:
                return {"success": False, "error": "access_denied"}
            
            messages = await self.conversations.get_messages(conversation_id, limit)
            
            return {
                "success": True,
                "messages": messages
            }
        except Exception as e:
            raise Exception(f"Failed to get conversation history: {str(e)}")