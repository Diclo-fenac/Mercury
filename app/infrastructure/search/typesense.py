"""
Typesense Search Client
Layer 6: Infrastructure - Fuzzy/Keyword Search
"""
from typing import Dict, Any, Optional, List
import asyncio
import typesense

from app.utils.logger import get_logger

logger = get_logger("typesense")


class TypesenseClient:
    """Typesense client for fuzzy and keyword search"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8108,
        api_key: str = "xyz",
        protocol: str = "http"
    ):
        self.host = host
        self.port = port
        self.api_key = api_key
        self.protocol = protocol
        self.client = None
        self._connected = False
    
    async def connect(self) -> None:
        """Initialize Typesense client"""
        try:
            self.client = typesense.Client({
                'nodes': [{
                    'host': self.host,
                    'port': str(self.port),
                    'protocol': self.protocol
                }],
                'api_key': self.api_key,
                'connection_timeout_seconds': 2
            })
            
            # Test connection
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.client.collections.retrieve)
            
            self._connected = True
            logger.info(f"Typesense connected: {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Typesense: {e}")
            raise
    
    async def close(self) -> None:
        """Close Typesense connection"""
        self._connected = False
        logger.info("Typesense connection closed")
    
    async def health_check(self) -> bool:
        """Check Typesense health"""
        if not self._connected or not self.client:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.client.health.retrieve)
            return True
        except Exception as e:
            logger.error(f"Typesense health check failed: {e}")
            return False
    
    async def create_collection(self, schema: Dict[str, Any]) -> bool:
        """Create collection with schema"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.collections.create(schema)
            )
            logger.info(f"Created collection: {schema['name']}")
            return True
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return False
    
    async def collection_exists(self, name: str) -> bool:
        """Check if collection exists"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.collections[name].retrieve()
            )
            return True
        except:
            return False
    
    async def index_documents(self, collection: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk index documents"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.client.collections[collection].documents.import_(documents, {'action': 'upsert'})
            )
            
            success_count = sum(1 for r in result if r.get('success'))
            logger.info(f"Indexed {success_count}/{len(documents)} documents")
            
            return {
                "success": True,
                "total": len(documents),
                "indexed": success_count
            }
        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            return {"success": False, "error": str(e)}
    
    async def search(
        self,
        collection: str,
        query: str,
        query_by: str = "title,description,brand,category",
        filter_by: Optional[str] = None,
        sort_by: Optional[str] = None,
        per_page: int = 10,
        page: int = 1
    ) -> Dict[str, Any]:
        """Search documents with fuzzy matching"""
        try:
            search_params = {
                'q': query,
                'query_by': query_by,
                'per_page': per_page,
                'page': page,
                'typo_tokens_threshold': 1,
                'num_typos': 2,
                'prefix': True
            }
            
            if filter_by:
                search_params['filter_by'] = filter_by
            
            if sort_by:
                search_params['sort_by'] = sort_by
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.client.collections[collection].documents.search(search_params)
            )
            
            hits = result.get('hits', [])
            documents = [hit['document'] for hit in hits]
            
            return {
                "success": True,
                "documents": documents,
                "found": result.get('found', 0),
                "search_time_ms": result.get('search_time_ms', 0)
            }
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {"success": False, "error": str(e), "documents": []}
    
    async def multi_search(self, collection: str, searches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple searches in parallel"""
        try:
            search_requests = {
                'searches': [
                    {
                        'collection': collection,
                        **search
                    }
                    for search in searches
                ]
            }
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self.client.multi_search.perform(search_requests, {})
            )
            
            return results.get('results', [])
            
        except Exception as e:
            logger.error(f"Multi-search error: {e}")
            return []
    
    async def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        try:
            loop = asyncio.get_event_loop()
            doc = await loop.run_in_executor(
                None,
                lambda: self.client.collections[collection].documents[doc_id].retrieve()
            )
            return doc
        except Exception as e:
            logger.error(f"Error getting document: {e}")
            return None
    
    async def delete_collection(self, name: str) -> bool:
        """Delete collection"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.collections[name].delete()
            )
            logger.info(f"Deleted collection: {name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False
