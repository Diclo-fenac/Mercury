"""
Conversation Service - Layer 5: Domain
Pure business logic for conversations
"""
from typing import Dict, Any, Optional, List
from app.infrastructure.db.firestore import FirestoreClient
from app.infrastructure.cache.redis import RedisClient
from app.infrastructure.id_generator import IDGenerator


class ConversationService:
    """Conversation business logic"""
    
    def __init__(self, firestore: FirestoreClient, cache: Optional[RedisClient]):
        self.db = firestore
        self.cache = cache
        self.id_gen = IDGenerator()
    
    async def get_user_conversations(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's conversations"""
        filters = {'user_id': user_id}
        conversations = await self.db.query_collection('conversations', filters, limit)
        return conversations
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID"""
        return await self.db.get_document('conversations', conversation_id)
    
    async def create_conversation(self, user_id: str, title: Optional[str] = None) -> str:
        """Create new conversation"""
        conversation_id = self.id_gen.conversation_id(user_id)
        conversation_data = {
            'user_id': user_id,
            'title': title or 'New Conversation',
            'created_at': self.id_gen.timestamp(),
            'updated_at': self.id_gen.timestamp(),
            'message_count': 0
        }
        await self.db.set_document('conversations', conversation_id, conversation_data)
        return conversation_id
    
    async def save_message(
        self,
        conversation_id: str,
        user_id: str,
        message: str,
        role: str = 'user',
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save message to conversation"""
        message_id = self.id_gen.message_id()
        message_data = {
            'message_id': message_id,
            'conversation_id': conversation_id,
            'user_id': user_id,
            'message': message,
            'role': role,
            'timestamp': self.id_gen.timestamp(),
            'metadata': metadata or {}
        }
        
        await self.db.save_conversation_message(user_id, conversation_id, message_data)
        return message_id
    
    async def get_messages(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation messages"""
        return await self.db.get_conversation_messages(conversation_id, limit)
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation"""
        return await self.db.delete_document('conversations', conversation_id)
