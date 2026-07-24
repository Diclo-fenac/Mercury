from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional


class BaseAIProvider(ABC):
    """
    Abstract base class for LLM providers.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider."""
        pass

    @abstractmethod
    def register_tool(self, name: str, func: Callable, description: str, parameters: Dict[str, Any]):
        """Register a tool with the provider."""
        pass

    @abstractmethod
    async def generate_with_tools(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        tenant_context: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Generate response with tools.
        Returns a dictionary with success status, response text, and optional function call results.
        """
        pass

    @abstractmethod
    async def generate(self, prompt: str) -> Optional[str]:
        """Simple text generation without tools."""
        pass

    @abstractmethod
    async def analyze_image(self, image_data: str, prompt: Optional[str] = None) -> Optional[str]:
        """Analyze an image."""
        pass
