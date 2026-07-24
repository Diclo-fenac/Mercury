"""
CLIP Embedder - Layer 4: Add-ons
Generate multimodal embeddings locally for semantic image search.
"""
import asyncio
import random
from typing import List, Optional

from app.addons.embeddings.providers.base import BaseVisionEmbeddingProvider
from app.utils.logger import get_logger

logger = get_logger("clip_embedder")

class CLIPEmbedder(BaseVisionEmbeddingProvider):
    """Generate image and text embeddings locally using CLIP for semantic image search"""

    def __init__(self, model_name: str = "clip-ViT-B-32"):
        self.model_name = model_name
        self.model = None
        self._initialized = False

    async def initialize(self) -> None:
        """Load model into memory (runs once at startup)"""
        pass

    async def _load_model(self) -> None:
        if self._initialized or self.model:
            return
            
        from app.settings import get_settings
        settings = get_settings()
        if getattr(settings, 'MERCURY_MODE', 'standard') == 'lite':
            logger.info("MERCURY_MODE is lite, skipping CLIP model loading.")
            return

        try:
            from sentence_transformers import SentenceTransformer
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                lambda: SentenceTransformer(self.model_name)
            )
            self._initialized = True
            logger.info(f"CLIP embedder initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load CLIP model {self.model_name}: {e}. Falling back to mock.")
            self.model = None
            self._initialized = False

    def _mock_vector(self, seed: str) -> List[float]:
        rng = random.Random(seed)
        vector = [rng.uniform(-1.0, 1.0) for _ in range(512)]
        norm = sum(x**2 for x in vector)**0.5
        return [x / norm for x in vector] if norm > 0 else [1.0] + [0.0] * 511

    async def embed_text(self, text: str, task_type: str = "retrieval_document") -> Optional[List[float]]:
        await self._load_model()
        if not self._initialized or not self.model:
            return self._mock_vector(text)

        try:
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(None, lambda: self.model.encode(text).tolist())
            return embedding
        except Exception as e:
            logger.error(f"Failed to encode text with CLIP: {e}")
            return self._mock_vector(text)

    async def embed_query(self, text: str) -> Optional[List[float]]:
        return await self.embed_text(text)

    async def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        await self._load_model()
        if not self._initialized or not self.model:
            return [self._mock_vector(t) for t in texts]

        try:
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(None, lambda: self.model.encode(texts).tolist())
            return embeddings
        except Exception as e:
            logger.error(f"Failed to encode batch with CLIP: {e}")
            return [self._mock_vector(t) for t in texts]
            
    async def embed_image(self, image_data: str) -> Optional[List[float]]:
        """Generate a 512-dim embedding for an image"""
        await self._load_model()
        if not self._initialized or not self.model:
            return self._mock_vector(image_data[:50])
            
        try:
            import base64
            import io

            from PIL import Image
            
            # parse base64
            if image_data.startswith('data:image/'):
                _, data = image_data.split(',', 1)
            else:
                data = image_data
                
            image_bytes = base64.b64decode(data)
            img = Image.open(io.BytesIO(image_bytes))
            
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(None, lambda: self.model.encode(img).tolist())
            return embedding
        except Exception as e:
            logger.error(f"Failed to encode image with CLIP: {e}")
            return self._mock_vector(image_data[:50])
