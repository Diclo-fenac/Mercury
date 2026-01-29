"""
Gemini Embeddings - Layer 4: Add-ons
Generate embeddings for semantic search
"""
import asyncio
from typing import List, Optional
import google.generativeai as genai

from app.utils.logger import get_logger

logger = get_logger("embeddings")


class GeminiEmbeddings:
    """Generate embeddings using Gemini text-embedding-004"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Gemini embeddings"""
        try:
            genai.configure(api_key=self.api_key)
            self._initialized = True
            logger.info("Gemini embeddings initialized")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            raise
    
    async def embed_text(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        if not self._initialized:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: genai.embed_content(
                    model="models/text-embedding-004",
                    content=text,
                    task_type="retrieval_query"
                )
            )
            
            return result['embedding']
            
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return None
    
    async def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts"""
        tasks = [self.embed_text(text) for text in texts]
        return await asyncio.gather(*tasks)
