"""Embeddings add-ons layer"""

from .clip_embedder import CLIPEmbedder
from .gemini import GeminiEmbeddings
from .local_embedder import LocalEmbedder

__all__ = ["GeminiEmbeddings", "LocalEmbedder", "CLIPEmbedder"]
