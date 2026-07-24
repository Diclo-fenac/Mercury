from app.addons.embeddings.gemini import GeminiEmbeddings
from app.addons.embeddings.local_embedder import LocalEmbedder
from app.addons.embeddings.providers.base import BaseEmbeddingProvider
from app.settings import Settings
from app.utils.logger import get_logger

logger = get_logger("embedding_factory")

class EmbeddingProviderFactory:
    """Factory for creating embedding providers based on configuration."""
    
    @staticmethod
    def create_provider(settings: Settings) -> BaseEmbeddingProvider:
        """Create and return the configured embedding provider."""
        provider_type = getattr(settings, "EMBEDDING_PROVIDER", "gemini").lower()
        
        if provider_type == "gemini":
            logger.info("Instantiating Gemini Embedding provider")
            api_key = settings.GOOGLE_API_KEY
            model = settings.GEMINI_EMBEDDING_MODEL
            return GeminiEmbeddings(api_key=api_key, model=model)
        elif provider_type == "local":
            logger.info("Instantiating Local Embedding provider")
            return LocalEmbedder()
        else:
            logger.warning(f"Unknown Embedding provider type '{provider_type}', falling back to Local")
            return LocalEmbedder()
