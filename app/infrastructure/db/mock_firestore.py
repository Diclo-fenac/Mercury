"""
Mock Firestore Client for Graceful Degradation
Used when real Firestore is unavailable
"""
from typing import Any, Dict, List, Optional

from app.utils.logger import get_logger

logger = get_logger("mock_firestore")


class MockFirestoreClient:
    """Mock Firestore client that provides empty responses"""
    
    def __init__(self):
        self._connected = False
        logger.warning("Using MockFirestoreClient - limited functionality")
    
    async def connect(self) -> None:
        """Mock connection"""
        self._connected = True
        logger.info("MockFirestoreClient 'connected'")
    
    async def close(self) -> None:
        """Mock close"""
        self._connected = False
        logger.info("MockFirestoreClient 'closed'")
    
    async def health_check(self) -> bool:
        """Mock health check"""
        return False  # Always report unhealthy since it's a mock
    
    # Document Operations
    async def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Mock get document - returns None"""
        logger.debug(f"MockFirestore: get_document({collection}, {doc_id}) -> None")
        return None
    
    async def set_document(
        self, 
        collection: str, 
        doc_id: str, 
        data: Dict[str, Any],
        merge: bool = False
    ) -> bool:
        """Mock set document - returns False"""
        logger.debug(f"MockFirestore: set_document({collection}, {doc_id}) -> False")
        return False
    
    async def update_document(
        self, 
        collection: str, 
        doc_id: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Mock update document - returns False"""
        logger.debug(f"MockFirestore: update_document({collection}, {doc_id}) -> False")
        return False
    
    async def delete_document(self, collection: str, doc_id: str) -> bool:
        """Mock delete document - returns False"""
        logger.debug(f"MockFirestore: delete_document({collection}, {doc_id}) -> False")
        return False
    
    # Query Operations
    async def query_collection(
        self, 
        collection: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Mock query collection - returns empty list"""
        logger.debug(f"MockFirestore: query_collection({collection}) -> []")
        return []
    
    async def count_documents(
        self, 
        collection: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Mock count documents - returns 0"""
        logger.debug(f"MockFirestore: count_documents({collection}) -> 0")
        return 0
    
    # Batch Operations
    async def batch_write(
        self, 
        collection: str,
        operations: List[Dict[str, Any]]
    ) -> bool:
        """Mock batch write - returns False"""
        logger.debug(f"MockFirestore: batch_write({collection}) -> False")
        return False
    
    # Subcollection Operations
    async def add_to_subcollection(
        self, 
        parent_collection: str,
        parent_doc_id: str,
        subcollection: str,
        data: Dict[str, Any]
    ) -> Optional[str]:
        """Mock add to subcollection - returns None"""
        logger.debug(f"MockFirestore: add_to_subcollection({parent_collection}/{parent_doc_id}/{subcollection}) -> None")
        return None
    
    async def get_subcollection(
        self, 
        parent_collection: str,
        parent_doc_id: str,
        subcollection: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Mock get subcollection - returns empty list"""
        logger.debug(f"MockFirestore: get_subcollection({parent_collection}/{parent_doc_id}/{subcollection}) -> []")
        return []
    
    # Application-Specific Methods
    async def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Mock get product - returns None"""
        logger.debug(f"MockFirestore: get_product_by_id({product_id}) -> None")
        return None
    
    async def search_products(
        self, 
        filters: Dict[str, Any], 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Mock search products - returns empty list"""
        logger.debug(f"MockFirestore: search_products({filters}) -> []")
        return []
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Mock get user profile - returns basic profile"""
        logger.debug(f"MockFirestore: get_user_profile({user_id}) -> mock_profile")
        # Return a basic mock profile so user operations don't completely fail
        return {
            "id": user_id,
            "preferences": {},
            "activity_summary": {},
            "created_at": "2024-01-01T00:00:00Z",
            "last_active": "2024-01-01T00:00:00Z"
        }
    
    async def update_user_preferences(
        self, 
        user_id: str, 
        preferences: Dict[str, Any]
    ) -> bool:
        """Mock update user preferences - returns False"""
        logger.debug(f"MockFirestore: update_user_preferences({user_id}) -> False")
        return False
    
    async def log_user_activity(self, activity_data: Dict[str, Any]) -> Optional[str]:
        """Mock log user activity - returns None"""
        logger.debug("MockFirestore: log_user_activity() -> None")
        return None
    
    async def get_user_activity(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Mock get user activity - returns empty list"""
        logger.debug(f"MockFirestore: get_user_activity({user_id}) -> []")
        return []
    
    async def save_conversation_message(
        self,
        user_id: str,
        conversation_id: str,
        message_data: Dict[str, Any]
    ) -> bool:
        """Mock save conversation message - returns False"""
        logger.debug(f"MockFirestore: save_conversation_message({conversation_id}) -> False")
        return False
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Mock get conversation messages - returns empty list"""
        logger.debug(f"MockFirestore: get_conversation_messages({conversation_id}) -> []")
        return []