"""
Firestore Database Client
Layer 6: Infrastructure - Data & State
Pure CRUD operations, no business logic
"""
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from app.utils.logger import get_logger

logger = get_logger("firestore")


class FirestoreClient:
    """Async Firestore database client wrapper"""
    
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
        self._connected = False
    
    async def connect(self) -> None:
        """Initialize Firestore client"""
        try:
            # Initialize Firestore client with credentials
            if self.credentials_path:
                logger.info(f"Initializing Firestore with credentials: {self.credentials_path}")
                self.db = firestore.Client.from_service_account_json(
                    self.credentials_path,
                    project=self.project_id
                )
            else:
                logger.info("Initializing Firestore with default credentials")
                self.db = firestore.Client(project=self.project_id)
            
            # Test connection
            await self._test_connection()
            
            self._connected = True
            logger.info("✅ Firestore service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firestore: {e}")
            raise
    
    async def close(self) -> None:
        """Close Firestore connection"""
        if self.db:
            self.db.close()
        self._connected = False
        logger.info("✅ Firestore connection closed")
    
    async def health_check(self) -> bool:
        """Check Firestore health"""
        if not self._connected or not self.db:
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
    
    # ==================== Document Operations ====================
    
    async def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        try:
            if not self.db:
                return None
            
            loop = asyncio.get_event_loop()
            doc = await loop.run_in_executor(
                None,
                lambda: self.db.collection(collection).document(doc_id).get()
            )
            
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting document {doc_id} from {collection}: {e}")
            return None
    
    async def set_document(
        self, 
        collection: str, 
        doc_id: str, 
        data: Dict[str, Any],
        merge: bool = False
    ) -> bool:
        """Set document"""
        try:
            if not self.db:
                return False
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.db.collection(collection).document(doc_id).set(data, merge=merge)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting document {doc_id} in {collection}: {e}")
            return False
    
    async def update_document(
        self, 
        collection: str, 
        doc_id: str, 
        data: Dict[str, Any]
    ) -> bool:
        """Update document"""
        try:
            if not self.db:
                return False
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.db.collection(collection).document(doc_id).update(data)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating document {doc_id} in {collection}: {e}")
            return False
    
    async def delete_document(self, collection: str, doc_id: str) -> bool:
        """Delete document"""
        try:
            if not self.db:
                return False
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.db.collection(collection).document(doc_id).delete()
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {doc_id} from {collection}: {e}")
            return False
    
    # ==================== Query Operations ====================
    
    async def query_collection(
        self, 
        collection: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query collection with filters"""
        try:
            if not self.db:
                return []
            
            query = self.db.collection(collection)
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if value is not None:
                        query = query.where(
                            filter=FieldFilter(field, '==', value)
                        )
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            # Execute query
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(None, lambda: list(query.get()))
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying collection {collection}: {e}")
            return []
    
    async def count_documents(
        self, 
        collection: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count documents in collection"""
        try:
            if not self.db:
                return 0
            
            query = self.db.collection(collection)
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if value is not None:
                        query = query.where(
                            filter=FieldFilter(field, '==', value)
                        )
            
            # Execute count
            loop = asyncio.get_event_loop()
            count = await loop.run_in_executor(
                None,
                lambda: query.count().get()[0][0].value
            )
            
            return count
            
        except Exception as e:
            logger.error(f"Error counting documents in {collection}: {e}")
            return 0
    
    # ==================== Batch Operations ====================
    
    async def batch_write(
        self, 
        collection: str,
        operations: List[Dict[str, Any]]
    ) -> bool:
        """Batch write operations"""
        try:
            if not self.db:
                return False
            
            batch = self.db.batch()
            
            for op in operations:
                op_type = op.get('type')  # 'set', 'update', 'delete'
                doc_id = op.get('doc_id')
                data = op.get('data', {})
                
                doc_ref = self.db.collection(collection).document(doc_id)
                
                if op_type == 'set':
                    batch.set(doc_ref, data, merge=op.get('merge', False))
                elif op_type == 'update':
                    batch.update(doc_ref, data)
                elif op_type == 'delete':
                    batch.delete(doc_ref)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, batch.commit)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in batch write to {collection}: {e}")
            return False
    
    # ==================== Subcollection Operations ====================
    
    async def add_to_subcollection(
        self, 
        parent_collection: str,
        parent_doc_id: str,
        subcollection: str,
        data: Dict[str, Any]
    ) -> Optional[str]:
        """Add document to subcollection"""
        try:
            if not self.db:
                return None
            
            loop = asyncio.get_event_loop()
            doc_ref = await loop.run_in_executor(
                None,
                lambda: self.db.collection(parent_collection)
                    .document(parent_doc_id)
                    .collection(subcollection)
                    .add(data)
            )
            
            return doc_ref[1].id
            
        except Exception as e:
            logger.error(f"Error adding to subcollection {subcollection}: {e}")
            return None
    
    async def get_subcollection(
        self, 
        parent_collection: str,
        parent_doc_id: str,
        subcollection: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get documents from subcollection"""
        try:
            if not self.db:
                return []
            
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(
                None,
                lambda: list(
                    self.db.collection(parent_collection)
                        .document(parent_doc_id)
                        .collection(subcollection)
                        .offset(offset)
                        .limit(limit)
                        .get()
                )
            )
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting subcollection {subcollection}: {e}")
            return []
    
    # ==================== Application-Specific Methods ====================
    
    async def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        return await self.get_document(self.collection_name, product_id)
    
    async def search_products(
        self, 
        filters: Dict[str, Any], 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search products with filters"""
        return await self.query_collection(self.collection_name, filters, limit)
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        return await self.get_document('users', user_id)
    
    async def update_user_preferences(
        self, 
        user_id: str, 
        preferences: Dict[str, Any]
    ) -> bool:
        """Update user preferences"""
        return await self.update_document('users', user_id, {
            'preferences': preferences,
            'updated_at': datetime.now()
        })
    
    async def log_user_activity(self, activity_data: Dict[str, Any]) -> Optional[str]:
        """Log user activity"""
        user_id = activity_data.get('user_id')
        if not user_id:
            return None
        
        return await self.add_to_subcollection('users', user_id, 'activities', activity_data)
    
    async def get_user_activity(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get user activity history"""
        return await self.get_subcollection('users', user_id, 'activities', limit)
    
    async def save_conversation_message(
        self,
        user_id: str,
        conversation_id: str,
        message_data: Dict[str, Any]
    ) -> bool:
        """Save conversation message"""
        # Save message to subcollection
        message_id = message_data.get('message_id')
        if not message_id:
            return False
        
        success = await self.set_document(
            f'conversations/{conversation_id}/messages',
            message_id,
            message_data
        )
        
        if success:
            # Update conversation metadata
            await self.update_document('conversations', conversation_id, {
                'user_id': user_id,
                'last_message_at': datetime.now(),
                'message_count': firestore.Increment(1)
            })
        
        return success
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get conversation messages"""
        return await self.get_subcollection(
            'conversations',
            conversation_id,
            'messages',
            limit,
            offset
        )
