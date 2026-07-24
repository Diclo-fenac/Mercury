import asyncio
from types import SimpleNamespace

import pytest

from app.addons.embeddings.gemini import EMBEDDING_DIMENSION, GeminiEmbeddings
from app.addons.embeddings.local_embedder import LocalEmbedder
from app.addons.embeddings.providers.base import BaseEmbeddingProvider
from app.addons.embeddings.providers.factory import EmbeddingProviderFactory
from app.settings import Settings


def test_embedding_provider_factory_gemini():
    settings = Settings(
        POSTGRES_PASSWORD="dummy",
        TYPESENSE_API_KEY="dummy",
        GOOGLE_API_KEY="dummy_key",
        EMBEDDING_PROVIDER="gemini"
    )
    
    provider = EmbeddingProviderFactory.create_provider(settings)
    assert isinstance(provider, BaseEmbeddingProvider)
    assert isinstance(provider, GeminiEmbeddings)
    assert provider.api_key == "dummy_key"
    assert provider.model == "gemini-embedding-2"


@pytest.mark.asyncio
async def test_gemini_embedding_2_uses_schema_dimension_without_task_type(monkeypatch):
    class FakeModels:
        def __init__(self):
            self.kwargs = None

        def embed_content(self, **kwargs):
            self.kwargs = kwargs
            return SimpleNamespace(
                embeddings=[SimpleNamespace(values=[0.1] * EMBEDDING_DIMENSION)]
            )

    models = FakeModels()
    provider = GeminiEmbeddings(api_key="configured")
    provider._client = SimpleNamespace(models=models)
    provider._initialized = True

    class ImmediateLoop:
        async def run_in_executor(self, _executor, function):
            return function()

    monkeypatch.setattr(asyncio, "get_event_loop", lambda: ImmediateLoop())
    vector = await provider.embed_query("laptop")

    assert len(vector) == EMBEDDING_DIMENSION
    assert models.kwargs["model"] == "gemini-embedding-2"
    assert models.kwargs["config"].output_dimensionality == EMBEDDING_DIMENSION
    assert models.kwargs["config"].task_type is None


@pytest.mark.asyncio
async def test_gemini_fallback_matches_typesense_dimension():
    provider = GeminiEmbeddings(api_key="")
    await provider.initialize()

    assert len(await provider.embed_text("laptop")) == EMBEDDING_DIMENSION

def test_embedding_provider_factory_local():
    settings = Settings(
        POSTGRES_PASSWORD="dummy",
        TYPESENSE_API_KEY="dummy",
        EMBEDDING_PROVIDER="local"
    )
    
    provider = EmbeddingProviderFactory.create_provider(settings)
    assert isinstance(provider, BaseEmbeddingProvider)
    assert isinstance(provider, LocalEmbedder)
