import pytest

from app.intelligence.engine import LLMEngine
from app.intelligence.providers.base import BaseAIProvider
from app.intelligence.providers.factory import AIProviderFactory
from app.settings import Settings


def test_ai_provider_factory_gemini():
    settings = Settings(
        POSTGRES_PASSWORD="dummy",
        TYPESENSE_API_KEY="dummy",
        GOOGLE_API_KEY="dummy_key",
        AI_PROVIDER="gemini"
    )
    
    provider = AIProviderFactory.create_provider(settings)
    assert isinstance(provider, BaseAIProvider)
    assert isinstance(provider, LLMEngine)
    assert provider.api_key == "dummy_key"

def test_ai_provider_factory_fallback():
    settings = Settings(
        POSTGRES_PASSWORD="dummy",
        TYPESENSE_API_KEY="dummy",
        GOOGLE_API_KEY="dummy_key",
        AI_PROVIDER="unknown"
    )
    
    provider = AIProviderFactory.create_provider(settings)
    assert isinstance(provider, BaseAIProvider)
    # Should fallback to Gemini
    assert isinstance(provider, LLMEngine)
