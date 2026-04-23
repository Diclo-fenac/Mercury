"""
Qdrant Vector Database Client
Layer 6: Infrastructure - Data & State
Pure CRUD operations for vector search, no business logic
"""
from typing import Any, Dict, List, Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.utils.logger import get_logger

logger = get_logger("qdrant")


class QdrantClient:
    """Async Qdrant vector database client"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        api_key: Optional[str] = None,
        collection_name: str = "products"
    ):
        self.host = host
        self.port = port
        self.api_key = api_key
        self.collection_name = collection_name
        self.client: Optional[AsyncQdrantClient] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Initialize Qdrant client"""
        try:
            # Use HTTP for local development, HTTPS for production
            url = f"http://{self.host}:{self.port}"
            
            self.client = AsyncQdrantClient(
                url=url,
                api_key=self.api_key,
                prefer_grpc=False  # Use HTTP instead of gRPC
            )
            
            # Test connection
            await self.client.get_collections()
            self._connected = True
            
            logger.info(f"✅ Qdrant connected: {url}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            # Don't raise - allow app to start without Qdrant
            self._connected = False
    
    async def close(self) -> None:
        """Close Qdrant connection"""
        if self.client:
            await self.client.close()
        self._connected = False
        logger.info("✅ Qdrant connection closed")
    
    async def health_check(self) -> bool:
        """Check Qdrant health"""
        if not self._connected or not self.client:
            return False
        
        try:
            await self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False
    
    # ==================== Collection Operations ====================
    
    async def create_collection(
        self,
        collection_name: str,
        vector_size: int = 1536,
        distance: Distance = Distance.COSINE
    ) -> bool:
        """Create a new collection"""
        try:
            if not self.client:
                return False
            
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=distance)
            )
            
            logger.info(f"✅ Created collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            return False
    
    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection"""
        try:
            if not self.client:
                return False
            
            await self.client.delete_collection(collection_name)
            logger.info(f"✅ Deleted collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {e}")
            return False
    
    async def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists"""
        try:
            if not self.client:
                return False
            
            collections = await self.client.get_collections()
            return any(c.name == collection_name for c in collections.collections)
            
        except Exception as e:
            logger.error(f"Error checking collection {collection_name}: {e}")
            return False
    
    # ==================== Point Operations ====================
    
    async def upsert_point(
        self,
        collection_name: str,
        point_id: int,
        vector: List[float],
        payload: Dict[str, Any]
    ) -> bool:
        """Upsert a single point"""
        try:
            if not self.client:
                return False
            
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )
            
            await self.client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error upserting point in {collection_name}: {e}")
            return False
    
    async def upsert_points(
        self,
        collection_name: str,
        points: List[Dict[str, Any]]
    ) -> bool:
        """Upsert multiple points"""
        try:
            if not self.client:
                return False
            
            point_structs = [
                PointStruct(
                    id=p['id'],
                    vector=p['vector'],
                    payload=p.get('payload', {})
                )
                for p in points
            ]
            
            await self.client.upsert(
                collection_name=collection_name,
                points=point_structs
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error upserting points in {collection_name}: {e}")
            return False
    
    async def delete_point(self, collection_name: str, point_id: int) -> bool:
        """Delete a point"""
        try:
            if not self.client:
                return False
            
            await self.client.delete(
                collection_name=collection_name,
                points_selector=[point_id]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting point from {collection_name}: {e}")
            return False
    
    async def get_point(
        self,
        collection_name: str,
        point_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get a point by ID"""
        try:
            if not self.client:
                return None
            
            point = await self.client.retrieve(
                collection_name=collection_name,
                ids=[point_id]
            )
            
            if point:
                return {
                    'id': point[0].id,
                    'vector': point[0].vector,
                    'payload': point[0].payload
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting point from {collection_name}: {e}")
            return None
    
    # ==================== Search Operations ====================
    
    async def search(
        self,
        collection_name: str,
        vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        try:
            if not self.client:
                return []
            
            results = await self.client.search(
                collection_name=collection_name,
                query_vector=vector,
                limit=limit,
                score_threshold=score_threshold
            )
            
            return [
                {
                    'id': r.id,
                    'score': r.score,
                    'payload': r.payload
                }
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"Error searching in {collection_name}: {e}")
            return []
    
    async def search_batch(
        self,
        collection_name: str,
        vectors: List[List[float]],
        limit: int = 10
    ) -> List[List[Dict[str, Any]]]:
        """Batch search for similar vectors"""
        try:
            if not self.client:
                return []
            
            results = await self.client.search_batch(
                collection_name=collection_name,
                requests=[
                    {
                        'vector': vector,
                        'limit': limit
                    }
                    for vector in vectors
                ]
            )
            
            return [
                [
                    {
                        'id': r.id,
                        'score': r.score,
                        'payload': r.payload
                    }
                    for r in batch_results
                ]
                for batch_results in results
            ]
            
        except Exception as e:
            logger.error(f"Error batch searching in {collection_name}: {e}")
            return []
    
    # ==================== Payload Operations ====================
    
    async def set_payload(
        self,
        collection_name: str,
        point_ids: List[int],
        payload: Dict[str, Any]
    ) -> bool:
        """Set payload for points"""
        try:
            if not self.client:
                return False
            
            await self.client.set_payload(
                collection_name=collection_name,
                payload=payload,
                points=point_ids
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting payload in {collection_name}: {e}")
            return False
    
    async def delete_payload(
        self,
        collection_name: str,
        point_ids: List[int],
        keys: List[str]
    ) -> bool:
        """Delete payload keys from points"""
        try:
            if not self.client:
                return False
            
            await self.client.delete_payload(
                collection_name=collection_name,
                keys=keys,
                points=point_ids
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting payload from {collection_name}: {e}")
            return False
    
    # ==================== Collection Stats ====================
    
    async def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get collection information"""
        try:
            if not self.client:
                return None
            
            info = await self.client.get_collection(collection_name)
            
            return {
                'name': collection_name,
                'points_count': info.points_count,
                'vectors_count': info.indexed_vectors_count,  # Use indexed_vectors_count
                'config': info.config
            }
            
        except Exception as e:
            logger.error(f"Error getting collection info for {collection_name}: {e}")
            return None
    
    async def get_collection_stats(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get collection statistics"""
        try:
            if not self.client:
                return None
            
            info = await self.get_collection_info(collection_name)
            
            if not info:
                return None
            
            return {
                'collection_name': collection_name,
                'total_points': info.get('points_count', 0),
                'total_vectors': info.get('vectors_count', 0),
                'status': 'active'
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats for {collection_name}: {e}")
            return None
