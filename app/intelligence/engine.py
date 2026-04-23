"""
LLM Engine - Layer 3: Intelligence
Google Gemini integration with function calling
"""
import asyncio
from typing import Any, Callable, Dict, Optional

import google.genai as genai

from app.utils.logger import get_logger

logger = get_logger("llm")


class LLMEngine:
    """LLM runtime using Google Gemini with function calling"""
    
    def __init__(self, api_key: str, project_id: Optional[str] = None):
        self.api_key = api_key
        self.project_id = project_id
        self.client = None
        self.model = None
        self.tools = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Gemini client"""
        try:
            # Initialize client with API key
            self.client = genai.Client(api_key=self.api_key)
            self.model = "gemini-2.5-flash"
            self._initialized = True
            logger.info("✅ LLM engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            # Don't raise - allow app to start without LLM
            self._initialized = False
    
    def register_tool(self, name: str, func: Callable, description: str, parameters: Dict[str, Any]):
        """Register a function calling tool"""
        self.tools[name] = {
            'function': func,
            'description': description,
            'parameters': parameters
        }
    
    async def generate_with_tools(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate response with function calling"""
        if not self._initialized or not self.client:
            return {"success": False, "error": "Model not initialized"}
        
        try:
            # Build full prompt with context
            full_prompt = self._build_prompt(prompt, context)
            
            # Generate response
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.model,
                    contents=full_prompt
                )
            )
            
            # Return response
            return {
                "success": True,
                "response": response.text if response else "",
                "function_called": None
            }
            
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return {"success": False, "error": str(e)}
    
    def _build_prompt(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Build prompt with context"""
        parts = [
            "You are a helpful shopping assistant for Mercury.",
            "Help users find products, answer questions, and provide recommendations.",
            ""
        ]
        
        if context:
            if context.get('user_preferences'):
                parts.append(f"User preferences: {context['user_preferences']}")
            if context.get('recent_messages'):
                parts.append("Recent conversation:")
                for msg in context['recent_messages'][-3:]:
                    parts.append(f"{msg.get('role', 'user')}: {msg.get('message', '')}")
                parts.append("")
        
        parts.append(f"User: {message}")
        parts.append("Assistant:")
        
        return "\n".join(parts)
    
    async def generate(self, prompt: str) -> Optional[str]:
        """Simple generation without tools"""
        if not self._initialized or not self.client:
            return None
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
            )
            return response.text if response else None
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return None
    
    async def analyze_image(self, image_data: str, prompt: str = None) -> Optional[str]:
        """Analyze image with Gemini Vision"""
        if not self._initialized or not self.client:
            return None
        
        try:
            import base64
            from io import BytesIO

            from PIL import Image
            
            # Decode base64 image
            if image_data.startswith('data:image/'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(BytesIO(image_bytes))
            
            default_prompt = "Analyze this image and describe what you see. If it's a product, identify key features, brand, and type."
            analysis_prompt = prompt or default_prompt
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.model,
                    contents=[analysis_prompt, image]
                )
            )
            
            return response.text if response else None
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return None
