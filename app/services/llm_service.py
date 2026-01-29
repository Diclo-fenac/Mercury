"""
LLM Service
Google Gemini integration with async support
"""
import asyncio
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.services.container import ServiceInterface
from app.core.logging import get_logger

logger = get_logger("llm")

class LLMService(ServiceInterface):
    """Async LLM service using Google Gemini"""
    
    def __init__(self, api_key: str, project_id: Optional[str] = None):
        self.api_key = api_key
        self.project_id = project_id
        self.model = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize Gemini client"""
        try:
            # Configure Gemini
            genai.configure(api_key=self.api_key)
            
            # Initialize model
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                }
            )
            
            self._initialized = True
            logger.info("✅ Gemini LLM service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM service: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Cleanup LLM resources"""
        self._initialized = False
        logger.info("✅ LLM service cleaned up")
    
    async def health_check(self) -> bool:
        """Check LLM service health"""
        if not self._initialized or not self.model:
            return False
        
        try:
            # Simple test generation
            response = await self._generate_async("Test")
            return bool(response)
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False
    
    async def _generate_async(self, prompt: str, **kwargs) -> Optional[str]:
        """Generate response asynchronously"""
        if not self.model:
            return None
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.model.generate_content(prompt, **kwargs)
            )
            
            return response.text if response and response.text else None
            
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return None
    
    async def generate_chat_response(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate chat response with context"""
        try:
            # Build enhanced prompt
            prompt_parts = []
            
            # System context
            prompt_parts.append("""
You are an AI assistant for Walmart, helping customers find products and answer questions.
You have access to product information, user preferences, and shopping context.
Be helpful, friendly, and concise. Focus on providing relevant product recommendations.
""")
            
            # User context
            if user_profile:
                preferences = user_profile.get("preferences", {})
                if preferences:
                    prompt_parts.append(f"User preferences: {preferences}")
            
            # Conversation context
            if context and context.get("recent_messages"):
                prompt_parts.append("Recent conversation:")
                for msg in context["recent_messages"][-3:]:  # Last 3 messages
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    prompt_parts.append(f"{role}: {content}")
            
            # Current message
            prompt_parts.append(f"User: {message}")
            prompt_parts.append("Assistant:")
            
            full_prompt = "\n".join(prompt_parts)
            
            # Generate response
            response_text = await self._generate_async(full_prompt)
            
            if response_text:
                return {
                    "success": True,
                    "response": response_text,
                    "context_used": bool(context),
                    "personalized": bool(user_profile)
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to generate response"
                }
                
        except Exception as e:
            logger.error(f"Chat response generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_image(self, image_data: str) -> Dict[str, Any]:
        """Analyze image with Gemini Vision"""
        try:
            if not self.model:
                return {"success": False, "error": "Model not initialized"}
            
            # Prepare image for Gemini
            import base64
            import io
            from PIL import Image
            
            # Decode base64 image
            if image_data.startswith('data:image/'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Analyze image
            prompt = """
Analyze this image and provide:
1. A detailed description of what you see
2. If it's a product, identify the product type, brand, and key features
3. If it contains a barcode, mention that
4. Any relevant shopping or product information

Be specific and helpful for someone looking to find or buy this item.
"""
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content([prompt, image])
            )
            
            if response and response.text:
                return {
                    "success": True,
                    "description": response.text,
                    "analysis_type": "gemini_vision"
                }
            else:
                return {
                    "success": False,
                    "error": "No response from vision model"
                }
                
        except Exception as e:
            logger.error(f"Image analysis error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_query(
        self, 
        query: str, 
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze search query to extract intent and filters"""
        try:
            prompt = f"""
Analyze this search query and extract structured information:
Query: "{query}"

Provide a JSON response with:
- intent: the main search intent (product_search, question, comparison, etc.)
- category: likely product category
- sub_category: more specific category if applicable
- brand: any brand mentioned
- attributes: key product attributes mentioned (color, size, material, etc.)
- price_intent: any price-related intent (cheap, expensive, under $X, etc.)
- filters: suggested search filters
- semantic_query: optimized query for semantic search

User preferences: {user_preferences or 'None'}

Respond only with valid JSON.
"""
            
            response_text = await self._generate_async(prompt)
            
            if response_text:
                try:
                    import json
                    analysis = json.loads(response_text)
                    return {
                        "success": True,
                        "analysis": analysis
                    }
                except json.JSONDecodeError:
                    # Fallback to basic analysis
                    return {
                        "success": True,
                        "analysis": {
                            "intent": "product_search",
                            "semantic_query": query,
                            "original_query": query
                        }
                    }
            else:
                return {
                    "success": False,
                    "error": "Failed to analyze query"
                }
                
        except Exception as e:
            logger.error(f"Query analysis error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_product_summary(self, product: Dict[str, Any]) -> str:
        """Generate a natural language summary of a product"""
        try:
            prompt = f"""
Create a concise, helpful summary of this product for a customer:

Product: {product.get('title', 'Unknown Product')}
Brand: {product.get('brand', 'N/A')}
Category: {product.get('category', 'N/A')}
Price: ${product.get('price', {}).get('selling', 'N/A')}
Rating: {product.get('rating', 'N/A')}/5
Description: {product.get('description', 'No description available')[:200]}

Write a 2-3 sentence summary highlighting the key features and value proposition.
"""
            
            response = await self._generate_async(prompt)
            return response or f"This is a {product.get('title', 'product')} from {product.get('brand', 'the store')}."
            
        except Exception as e:
            logger.error(f"Product summary generation error: {e}")
            return f"Product: {product.get('title', 'Unknown')}"
    
    async def generate_personalized_recommendations(
        self, 
        user_profile: Dict[str, Any], 
        products: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate personalized product recommendations"""
        try:
            prompt = f"""
Based on this user profile, rank and explain these product recommendations:

User Profile:
- Preferences: {user_profile.get('preferences', {})}
- Recent Activity: {user_profile.get('recent_activity', [])}
- Purchase History: {user_profile.get('purchase_history', [])}

Products to rank:
{[p.get('title', 'Unknown') for p in products[:5]]}

Provide:
1. Ranked list of products (most to least relevant)
2. Brief explanation for each recommendation
3. Overall personalization strategy used

Keep explanations concise and customer-friendly.
"""
            
            response = await self._generate_async(prompt)
            
            if response:
                return {
                    "success": True,
                    "recommendations": response,
                    "personalized": True
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to generate recommendations"
                }
                
        except Exception as e:
            logger.error(f"Personalized recommendations error: {e}")
            return {
                "success": False,
                "error": str(e)
            }