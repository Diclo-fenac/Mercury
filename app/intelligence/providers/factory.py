from typing import Optional

from app.intelligence.engine import LLMEngine
from app.intelligence.providers.base import BaseAIProvider
from app.settings import Settings
from app.utils.logger import get_logger

logger = get_logger("ai_factory")

class AIProviderFactory:
    """Factory for creating AI providers based on configuration."""
    
    @staticmethod
    def create_provider(settings: Settings) -> BaseAIProvider:
        """Create and return the configured AI provider."""
        provider_type = getattr(settings, "AI_PROVIDER", "gemini").lower()
        
        if provider_type == "gemini":
            logger.info("Instantiating Gemini AI provider")
            api_key = settings.GOOGLE_API_KEY
            project_id = getattr(settings, "GOOGLE_CLOUD_PROJECT", None)
            return LLMEngine(api_key=api_key, project_id=project_id)
        elif provider_type == "openai":
            from app.intelligence.providers.openai import OpenAIProvider
            logger.info("Instantiating OpenAI AI provider")
            api_key = getattr(settings, "OPENAI_API_KEY", "dummy")
            return OpenAIProvider(api_key=api_key)
        else:
            logger.warning(f"Unknown AI provider type '{provider_type}', falling back to Gemini")
            return LLMEngine(api_key=settings.GOOGLE_API_KEY)
