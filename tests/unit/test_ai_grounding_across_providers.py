import pytest

from app.intelligence.providers.factory import AIProviderFactory
from app.settings import Settings


@pytest.mark.asyncio
async def test_openai_grounding_mock():
    settings = Settings(
        POSTGRES_PASSWORD="dummy",
        TYPESENSE_API_KEY="dummy",
        AI_PROVIDER="openai",
        OPENAI_API_KEY="dummy"
    )
    provider = AIProviderFactory.create_provider(settings)
    await provider.initialize()
    
    result = await provider.generate_with_tools("test query")
    assert result["success"] is True
    assert "[OpenAI]" in result["response"]
    assert result["function_called"] == "search_products"
