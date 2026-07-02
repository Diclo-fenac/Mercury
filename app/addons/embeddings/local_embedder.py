"""
Local Embedder - Layer 4: Add-ons
Generate embeddings locally using sentence-transformers (all-MiniLM-L6-v2) to eliminate API costs.
"""
import asyncio
import random
from typing import List, Optional
from app.utils.logger import get_logger

logger = get_logger("local_embedder")


class LocalEmbedder:
    """Generate embeddings locally using SentenceTransformers (all-MiniLM-L6-v2)"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self._initialized = False

    async def initialize(self) -> None:
        """Load model into memory (runs once at startup)"""
        pass  # Defer loading to first request

    async def _load_model(self) -> None:
        if self._initialized or self.model:
            return
            
        import os
        from app.settings import get_settings
        settings = get_settings()
        if getattr(settings, 'MERCURY_MODE', 'standard') == 'lite':
            logger.info("MERCURY_MODE is lite, skipping sentence-transformers loading.")
            return

        try:
            from sentence_transformers import SentenceTransformer
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                lambda: SentenceTransformer(self.model_name)
            )
            self._initialized = True
            logger.info(f"Local embedder initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load sentence-transformers model {self.model_name}: {e}. Falling back to mock embeddings.")
            self.model = None
            self._initialized = False

    async def embed_text(self, text: str, task_type: str = "retrieval_document") -> Optional[List[float]]:
        """Generate a 384-dim embedding for text"""
        await self._load_model()
        if not self._initialized or not self.model:
            # Fallback mock generator (384 dimensions)
            rng = random.Random(text)
            vector = [rng.uniform(-1.0, 1.0) for _ in range(384)]
            norm = sum(x**2 for x in vector)**0.5
            return [x / norm for x in vector] if norm > 0 else [1.0] + [0.0] * 383

        try:
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: self.model.encode(text).tolist()
            )
            return embedding
        except Exception as e:
            logger.error(f"Failed to encode text locally: {e}. Falling back to mock.")
            rng = random.Random(text)
            vector = [rng.uniform(-1.0, 1.0) for _ in range(384)]
            norm = sum(x**2 for x in vector)**0.5
            return [x / norm for x in vector] if norm > 0 else [1.0] + [0.0] * 383

    async def embed_query(self, text: str) -> Optional[List[float]]:
        """Generate a 384-dim embedding for a search query"""
        return await self.embed_text(text, task_type="retrieval_query")

    async def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate 384-dim embeddings for multiple texts"""
        if not self._initialized or not self.model:
            tasks = [self.embed_text(t) for t in texts]
            return await asyncio.gather(*tasks)

        try:
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self.model.encode(texts).tolist()
            )
            return embeddings
        except Exception as e:
            logger.error(f"Failed to encode batch locally: {e}. Falling back to mock batch.")
            tasks = [self.embed_text(t) for t in texts]
            return await asyncio.gather(*tasks)
