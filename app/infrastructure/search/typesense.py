"""
Typesense Search Client
Layer 6: Infrastructure - Fuzzy/Keyword Search
"""
import asyncio
from typing import Any, Dict, List, Optional

import typesense

from app.infrastructure.search.base import SearchAdapter
from app.utils.logger import get_logger

logger = get_logger("typesense")


class TypesenseClient(SearchAdapter):
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
            
    async def upsert_synonym(self, collection: str, synonym_id: str, synonyms: List[str], root: str = "") -> bool:
        """Upsert a synonym in Typesense"""
        try:
            mapping = {"synonyms": synonyms}
            if root:
                mapping["root"] = root
                
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.collections[collection].synonyms[synonym_id].upsert(mapping)
            )
            return True
        except Exception as e:
            logger.error(f"Error upserting synonym: {e}")
            return False
            
    async def delete_synonym(self, collection: str, synonym_id: str) -> bool:
        """Delete a synonym in Typesense"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.collections[collection].synonyms[synonym_id].delete()
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting synonym: {e}")
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
                "success": success_count == len(documents),
                "total": len(documents),
                "indexed": success_count,
                "failed": len(documents) - success_count,
                "results": result,
            }
        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            return {"success": False, "error": str(e)}

    async def delete_document(self, collection: str, document_id: str) -> bool:
        """Delete one derived search document; canonical data remains in PostgreSQL."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.collections[collection].documents[document_id].delete(),
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    async def search(
        self,
        collection: str,
        query: str,
        query_by: str = "title,description,brand,category",
        filter_by: Optional[str] = None,
        sort_by: Optional[str] = None,
        vector_query: Optional[str] = None,
        per_page: int = 10,
        page: int = 1,
        num_typos: int = 2,
        facet_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Search documents with fuzzy/hybrid matching"""
        try:
            search_params = {
                'q': query,
                'query_by': query_by,
                'per_page': per_page,
                'page': page,
                'typo_tokens_threshold': 1,
                'num_typos': num_typos,
                'prefix': True
            }
            
            if filter_by:
                search_params['filter_by'] = filter_by
            
            if sort_by:
                search_params['sort_by'] = sort_by
            if facet_by:
                search_params['facet_by'] = facet_by

            if vector_query:
                search_params['vector_query'] = vector_query
                search_requests = {
                    'searches': [
                        {
                            'collection': collection,
                            **search_params
                        }
                    ]
                }
                loop = asyncio.get_event_loop()
                multi_results = await loop.run_in_executor(
                    None,
                    lambda: self.client.multi_search.perform(search_requests, {})
                )
                result = multi_results.get('results', [{}])[0]
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self.client.collections[collection].documents.search(search_params)
                )
            
            hits = result.get('hits', [])
            documents = []
            for hit in hits:
                doc = dict(hit['document'])
                if 'vector_distance' in hit:
                    doc['vector_distance'] = hit['vector_distance']
                doc['_typesense'] = {
                    'text_match': hit.get('text_match'),
                    'text_match_info': hit.get('text_match_info'),
                    'vector_distance': hit.get('vector_distance'),
                }
                documents.append(doc)
            
            return {
                "success": True,
                "documents": documents,
                "found": result.get('found', 0),
                "search_time_ms": result.get('search_time_ms', 0),
                "facet_counts": result.get('facet_counts', []),
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

    async def get_suggestions(self, query: str, limit: int = 10, collection: str = "products") -> List[str]:
        """Get search autocomplete suggestions by querying collection"""
        try:
            res = await self.search(
                collection=collection,
                query=query,
                query_by="title,brand,category",
                per_page=limit
            )
            if res.get("success"):
                suggestions = []
                for doc in res.get("documents", []):
                    title = doc.get("title")
                    if title and title not in suggestions:
                        suggestions.append(title)
                return suggestions[:limit]
            return []
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            return []



    async def get_category_suggestions(self, query: str, limit: int = 5, collection: str = "products") -> List[Dict[str, str]]:
        """Get category suggestions based on query"""
        try:
            res = await self.search(
                collection=collection,
                query=query,
                query_by="category",
                per_page=limit * 2
            )
            if res.get("success"):
                categories = []
                seen = set()
                for doc in res.get("documents", []):
                    cat = doc.get("category")
                    if cat and cat not in seen:
                        seen.add(cat)
                        categories.append({"category": cat})
                return categories[:limit]
            return []
        except Exception as e:
            logger.error(f"Error getting category suggestions: {e}")
            return []

    async def get_brand_suggestions(self, query: str, limit: int = 5, collection: str = "products") -> List[Dict[str, str]]:
        """Get brand suggestions based on query"""
        try:
            res = await self.search(
                collection=collection,
                query=query,
                query_by="brand",
                per_page=limit * 2
            )
            if res.get("success"):
                brands = []
                seen = set()
                for doc in res.get("documents", []):
                    brand = doc.get("brand")
                    if brand and brand not in seen:
                        seen.add(brand)
                        brands.append({"brand": brand})
                return brands[:limit]
            return []
        except Exception as e:
            logger.error(f"Error getting brand suggestions: {e}")
            return []
