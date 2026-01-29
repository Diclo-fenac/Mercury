"""
Conversation Service
Conversation management and message handling
"""
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.container import ServiceInterface
from app.core.logging import get_logger

logger = get_logger("conversation")

class ConversationService(ServiceInterface):
    """Async conversation service"""
    
    def __init__(self):
        self.firestore_service = None
        self.redis_service = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize conversation service"""
        self._initialized = True
        logger.info("✅ Conversation service initialized")
    
    async def cleanup(self) -> None:
        """Cleanup conversation service"""
        self._initialized = False
        logger.info("✅ Conversation service cleaned up")
    
    async def health_check(self) -> bool:
        """Check conversation service health"""
        return self._initialized
    
    def set_dependencies(self, firestore_service, redis_service):
        """Set service dependencies"""
        self.firestore_service = firestore_service
        self.redis_service = redis_service
    
    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        archived: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Get user's conversations"""
        try:
            # Placeholder implementation
            # In production, this would query Firestore
            
            conversations = [
                {
                    "conversation_id": f"conv_{user_id}_1",
                    "title": "Product Search Chat",
                    "last_message": "Thanks for helping me find that laptop!",
                    "message_count": 15,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "archived": False
                },
                {
                    "conversation_id": f"conv_{user_id}_2", 
                    "title": "Shopping Assistant",
                    "last_message": "Can you help me find wireless headphones?",
                    "message_count": 8,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "archived": False
                }
            ]
            
            # Filter by archived status if specified
            if archived is not None:
                conversations = [c for c in conversations if c["archived"] == archived]
            
            # Apply pagination
            paginated = conversations[offset:offset + limit]
            
            return {
                "success": True,
                "conversations": paginated,
                "total": len(conversations)
            }
            
        except Exception as e:
            logger.error(f"Error getting conversations for {user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_conversation_details(
        self,
        user_id: str,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get detailed conversation information"""
        try:
            # Get messages from Firestore
            if self.firestore_service:
                messages = await self.firestore_service.get_conversation_messages(
                    conversation_id, limit, offset
                )
            else:
                # Placeholder messages
                messages = [
                    {
                        "message_id": "msg_1",
                        "user_id": user_id,
                        "message": "Hello, I need help finding a laptop",
                        "message_type": "text",
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {}
                    },
                    {
                        "message_id": "msg_2",
                        "user_id": "assistant",
                        "message": "I'd be happy to help you find a laptop! What's your budget and intended use?",
                        "message_type": "text",
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {}
                    }
                ]
            
            conversation = {
                "conversation_id": conversation_id,
                "title": "Product Search Chat",
                "messages": messages,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "archived": False,
                "metadata": {}
            }
            
            return {
                "success": True,
                "conversation": conversation
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation details: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def create_conversation(
        self,
        user_id: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new conversation"""
        try:
            conversation_id = f"conv_{user_id}_{uuid.uuid4().hex[:8]}"
            
            conversation_data = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "title": title or "New Conversation",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "archived": False,
                "metadata": metadata or {}
            }
            
            # Save to Firestore (placeholder)
            # In production: await self.firestore_service.create_conversation(conversation_data)
            
            return {
                "success": True,
                "conversation_id": conversation_id,
                "message": "Conversation created successfully",
                "created_at": conversation_data["created_at"]
            }
            
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def archive_conversation(
        self,
        user_id: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Archive a conversation"""
        try:
            # Update in Firestore (placeholder)
            # In production: await self.firestore_service.update_conversation(conversation_id, {"archived": True})
            
            return {
                "success": True,
                "message": "Conversation archived successfully"
            }
            
        except Exception as e:
            logger.error(f"Error archiving conversation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def unarchive_conversation(
        self,
        user_id: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Unarchive a conversation"""
        try:
            # Update in Firestore (placeholder)
            return {
                "success": True,
                "message": "Conversation unarchived successfully"
            }
            
        except Exception as e:
            logger.error(f"Error unarchiving conversation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_conversation(
        self,
        user_id: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Delete a conversation permanently"""
        try:
            # Delete from Firestore (placeholder)
            return {
                "success": True,
                "message": "Conversation deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def save_message(
        self,
        user_id: str,
        conversation_id: str,
        message_id: str,
        message: str,
        message_type: str = "text",
        role: str = "user",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Save a message to conversation"""
        try:
            message_data = {
                "message_id": message_id,
                "user_id": user_id,
                "conversation_id": conversation_id,
                "message": message,
                "message_type": message_type,
                "role": role,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # Save to Firestore
            if self.firestore_service:
                await self.firestore_service.save_conversation_message(
                    user_id, conversation_id, message_data
                )
            
            return {
                "success": True,
                "message_id": message_id
            }
            
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_conversation_history(
        self,
        user_id: str,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get conversation message history"""
        try:
            if self.firestore_service:
                messages = await self.firestore_service.get_conversation_messages(
                    conversation_id, limit, offset
                )
            else:
                # No Firestore service available - return empty but log warning
                logger.warning("Firestore service not available for conversation messages")
                messages = []
            
            return {
                "success": True,
                "messages": messages,
                "total": len(messages),
                "has_more": len(messages) == limit
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return {
                "success": False,
                "error": str(e)
            }