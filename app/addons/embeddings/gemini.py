"""
Gemini Embeddings - Layer 4: Add-ons
Generate embeddings for semantic search using google-genai SDK.
"""
import asyncio
from typing import List, Optional

from google import genai
from google.genai import types

from app.utils.logger import get_logger

logger = get_logger("embeddings")

EMBEDDING_MODEL = "models/gemini-embedding-001"


class GeminiEmbeddings:
    """Generate embeddings using Gemini text-embedding-002"""

    def __init__(self, api_key: str, model: str = EMBEDDING_MODEL):
        self.api_key = api_key
        self.model = model
        self._client: Optional[genai.Client] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize Gemini embeddings client"""
        try:
            if not self.api_key or self.api_key in ["your-google-api-key", "your-gemini-api-key", "dummy", "mock", ""] or not self.api_key.strip():
                logger.warning("⚠️ Using mock embeddings client (missing or placeholder API key)")
                self._client = None
                self._initialized = False
                return
            
            self._client = genai.Client(api_key=self.api_key)
            self._initialized = True
            logger.info(f"Gemini embeddings initialized (model={self.model})")
        except Exception as e:
            logger.warning(f"Failed to initialize embeddings: {e}. Falling back to mock embeddings.")
            self._client = None
            self._initialized = False

    async def embed_text(self, text: str, task_type: str = "retrieval_document") -> Optional[List[float]]:
        """Generate embedding for text"""
        if not self._initialized or not self._client:
            import random
            rng = random.Random(text)
            vector = [rng.uniform(-1.0, 1.0) for _ in range(768)]
            norm = sum(x**2 for x in vector)**0.5
            return [x / norm for x in vector] if norm > 0 else [1.0] + [0.0] * 767

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.models.embed_content(
                    model=self.model,
                    contents=text,
                    config=types.EmbedContentConfig(task_type=task_type),
                ),
            )
            return response.embeddings[0].values
        except Exception as e:
            logger.error(f"Embedding error: {e}. Falling back to mock embedding.")
            import random
            rng = random.Random(text)
            vector = [rng.uniform(-1.0, 1.0) for _ in range(768)]
            norm = sum(x**2 for x in vector)**0.5
            return [x / norm for x in vector] if norm > 0 else [1.0] + [0.0] * 767

    async def embed_query(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a search query"""
        return await self.embed_text(text, task_type="retrieval_query")

    async def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts"""
        tasks = [self.embed_text(t) for t in texts]
        return await asyncio.gather(*tasks)
