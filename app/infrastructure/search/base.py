"""
Base Search Engine Interface
Layer 6: Infrastructure - Search
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class SearchAdapter(ABC):
    """Abstract interface for Search Engines (e.g., Typesense, OpenSearch)"""
    
    @abstractmethod
    async def connect(self) -> None:
        pass
        
    @abstractmethod
    async def close(self) -> None:
        pass
        
    @abstractmethod
    async def health_check(self) -> bool:
        pass
        
    @abstractmethod
    async def create_collection(self, schema: Dict[str, Any]) -> bool:
        pass
        
    @abstractmethod
    async def collection_exists(self, name: str) -> bool:
        pass
        
    @abstractmethod
    async def index_documents(self, collection: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    async def delete_document(self, collection: str, document_id: str) -> bool:
        pass
        
    @abstractmethod
    async def delete_collection(self, name: str) -> bool:
        pass
        
    @abstractmethod
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
        pass
        
    @abstractmethod
    async def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        pass
