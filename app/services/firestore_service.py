"""
Firestore Service
Google Firestore database operations
"""
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.core.logging import get_logger
from app.services.container import ServiceInterface

logger = get_logger("firestore")

class FirestoreService(ServiceInterface):
    """Async Firestore service wrapper"""
    
    def __init__(
        self, 
        project_id: Optional[str] = None,
        credentials_path: Optional[str] = None,
        collection_name: str = "products"
    ):
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.collection_name = collection_name
        self.db = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Firestore client"""
        try:
            # Initialize Firestore client
            if self.credentials_path:
                self.db = firestore.Client.from_service_account_json(
                    self.credentials_path,
                    project=self.project_id
                )
            else:
                self.db = firestore.Client(project=self.project_id)
            
            # Test connection
            await self._test_connection()
            
            self._initialized = True
            logger.info("✅ Firestore service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firestore: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Cleanup Firestore resources"""
        if self.db:
            self.db.close()
        self._initialized = False
        logger.info("✅ Firestore service cleaned up")
    
    async def health_check(self) -> bool:
        """Check Firestore health"""
        if not self._initialized or not self.db:
            return False
        
        try:
            await self._test_connection()
            return True
        except Exception as e:
            logger.error(f"Firestore health check failed: {e}")
            return False
    
    async def _test_connection(self) -> None:
        """Test Firestore connection"""
        if not self.db:
            raise Exception("Firestore client not initialized")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: list(self.db.collection(self.collection_name).limit(1).get())
        )
    
    async def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        try:
            if not self.db:
                return None
            
            loop = asyncio.get_event_loop()
            doc = await loop.run_in_executor(
                None,
                lambda: self.db.collection(self.collection_name).document(product_id).get()
            )
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting product {product_id}: {e}")
            return None
    
    async def search_products(
        self, 
        filters: Dict[str, Any], 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search products with filters"""
        try:
            if not self.db:
                return []
            
            query = self.db.collection(self.collection_name)
            
            # Apply filters
            if filters.get('category'):
                query = query.where(
                    filter=FieldFilter('category', '==', filters['category'])
                )
            
            if filters.get('brand'):
                query = query.where(
                    filter=FieldFilter('brand', '==', filters['brand'])
                )
            
            if filters.get('stock_only'):
                query = query.where(
                    filter=FieldFilter('stock', '==', 'in_stock')
                )
            
            # Apply limit
            query = query.limit(limit)
            
            # Execute query
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(None, lambda: list(query.get()))
            
            products = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                products.append(data)
            
            return products
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        try:
            if not self.db:
                return None
            
            loop = asyncio.get_event_loop()
            doc = await loop.run_in_executor(
                None,
                lambda: self.db.collection('users').document(user_id).get()
            )
            
            if doc.exists:
                return doc.to_dict()
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user profile {user_id}: {e}")
            return None
    
    async def update_user_preferences(
        self, 
        user_id: str, 
        preferences: Dict[str, Any]
    ) -> None:
        """Update user preferences"""
        try:
            if not self.db:
                return
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.db.collection('users').document(user_id).set({
                    'preferences': preferences,
                    'updated_at': datetime.now()
                }, merge=True)
            )
            
        except Exception as e:
            logger.error(f"Error updating user preferences {user_id}: {e}")
            raise
    
    async def log_user_activity(self, activity_data: Dict[str, Any]) -> None:
        """Log user activity"""
        try:
            if not self.db:
                return
            
            user_id = activity_data.get('user_id')
            if not user_id:
                return
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.db.collection('users').document(user_id).collection('activities').add(activity_data)
            )
            
        except Exception as e:
            logger.error(f"Error logging user activity: {e}")
    
    async def get_user_activity(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user activity history"""
        try:
            if not self.db:
                return []
            
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(
                None,
                lambda: list(
                    self.db.collection('users')
                    .document(user_id)
                    .collection('activities')
                    .order_by('timestamp', direction=firestore.Query.DESCENDING)
                    .limit(limit)
                    .get()
                )
            )
            
            activities = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                activities.append(data)
            
            return activities
            
        except Exception as e:
            logger.error(f"Error getting user activity {user_id}: {e}")
            return []
    
    async def save_conversation_message(
        self,
        user_id: str,
        conversation_id: str,
        message_data: Dict[str, Any]
    ) -> None:
        """Save conversation message"""
        try:
            if not self.db:
                return
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: (
                    self.db.collection('conversations')
                    .document(conversation_id)
                    .collection('messages')
                    .document(message_data.get('message_id'))
                    .set(message_data)
                )
            )
            
            # Update conversation metadata
            await loop.run_in_executor(
                None,
                lambda: self.db.collection('conversations').document(conversation_id).set({
                    'user_id': user_id,
                    'last_message_at': datetime.now(),
                    'message_count': firestore.Increment(1)
                }, merge=True)
            )
            
        except Exception as e:
            logger.error(f"Error saving conversation message: {e}")
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get conversation messages"""
        try:
            if not self.db:
                return []
            
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(
                None,
                lambda: list(
                    self.db.collection('conversations')
                    .document(conversation_id)
                    .collection('messages')
                    .order_by('timestamp')
                    .offset(offset)
                    .limit(limit)
                    .get()
                )
            )
            
            messages = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                messages.append(data)
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting conversation messages: {e}")
            return []