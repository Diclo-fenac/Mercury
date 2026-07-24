from abc import ABC, abstractmethod
from typing import List, Optional


class BaseEmbeddingProvider(ABC):
    """
    Abstract base class for Embedding providers.
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider."""
        pass
        
    @abstractmethod
    async def embed_text(self, text: str, task_type: str = "retrieval_document") -> Optional[List[float]]:
        """Get the embedding vector for a single string for indexing."""
        pass

    @abstractmethod
    async def embed_query(self, text: str) -> Optional[List[float]]:
        """Get the embedding vector for a search query."""
        pass
        
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Get embedding vectors for a list of strings."""
        pass


class BaseVisionEmbeddingProvider(BaseEmbeddingProvider):
    """
    Abstract base class for vision/multimodal Embedding providers (e.g. CLIP).
    """

    @abstractmethod
    async def embed_image(self, image_data: str) -> Optional[List[float]]:
        """Get the embedding vector for an image (base64 or URL)."""
        pass

