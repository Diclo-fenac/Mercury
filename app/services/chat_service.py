"""
Chat Service
Handles chat message processing with AI integration
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.container import ServiceInterface

logger = get_logger("chat")

class ChatService(ServiceInterface):
    """Async chat service with AI integration"""
    
    def __init__(self):
        self.llm_service = None
        self.user_service = None
        self.conversation_service = None
        self.redis_service = None
        self.image_service = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize chat service with dependencies"""
        # Dependencies will be injected by container
        self._initialized = True
        logger.info("✅ Chat service initialized")
    
    async def cleanup(self) -> None:
        """Cleanup chat service"""
        self._initialized = False
        logger.info("✅ Chat service cleaned up")
    
    async def health_check(self) -> bool:
        """Check chat service health"""
        return self._initialized
    
    def set_dependencies(
        self,
        llm_service,
        user_service,
        conversation_service,
        redis_service,
        image_service
    ):
        """Set service dependencies"""
        self.llm_service = llm_service
        self.user_service = user_service
        self.conversation_service = conversation_service
        self.redis_service = redis_service
        self.image_service = image_service
    
    async def process_chat_message(
        self,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        message_type: str = "text",
        image_data: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process chat message with full AI integration
        
        Features:
        - Text and image message support
        - Conversation context management
        - User personalization
        - Caching for performance
        """
        try:
            # Generate message IDs
            user_message_id = f"msg_{uuid.uuid4().hex[:12]}"
            assistant_message_id = f"msg_{uuid.uuid4().hex[:12]}"
            
            # Create or get conversation ID
            if not conversation_id:
                conversation_id = f"conv_{user_id}_{int(datetime.now().timestamp())}"
            
            # Get user profile for personalization
            user_profile = None
            if self.user_service:
                profile_result = await self.user_service.get_user_profile(user_id)
                if profile_result.get("success"):
                    user_profile = profile_result.get("data")
            
            # Get conversation context
            context = await self._get_conversation_context(user_id, conversation_id)
            
            # Process based on message type
            if message_type == "image" and image_data:
                result = await self._process_image_message(
                    user_id, message, image_data, context, user_profile
                )
            else:
                result = await self._process_text_message(
                    user_id, message, context, user_profile
                )
            
            if not result.get("success"):
                return result
            
            # Save user message
            if self.conversation_service:
                await self.conversation_service.save_message(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    message_id=user_message_id,
                    message=message,
                    message_type=message_type,
                    role="user",
                    metadata=metadata or {}
                )
            
            # Save assistant message
            if self.conversation_service:
                await self.conversation_service.save_message(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    message_id=assistant_message_id,
                    message=result.get("response", ""),
                    message_type="text",
                    role="assistant",
                    metadata={
                        "personalized": result.get("personalized", False),
                        "context_used": result.get("context_used", False)
                    }
                )
            
            # Update conversation cache
            if self.redis_service:
                await self._update_conversation_cache(
                    user_id, conversation_id, user_message_id, assistant_message_id,
                    message, result.get("response", "")
                )
            
            # Log user activity
            if self.user_service:
                await self.user_service.log_activity(
                    user_id=user_id,
                    activity_type="chat_message",
                    metadata={
                        "conversation_id": conversation_id,
                        "message_type": message_type,
                        "response_generated": True
                    }
                )
            
            # Build final response
            return {
                "success": True,
                "response": result.get("response", ""),
                "conversation_id": conversation_id,
                "user_message_id": user_message_id,
                "assistant_message_id": assistant_message_id,
                "personalization_reason": result.get("personalization_reason"),
                "context_cached": bool(context),
                "features_used": {
                    "ai_response": True,
                    "personalization": result.get("personalized", False),
                    "context_awareness": result.get("context_used", False),
                    "caching": bool(self.redis_service),
                    "image_analysis": message_type == "image"
                },
                **result  # Include any additional data from processing
            }
            
        except Exception as e:
            logger.error(f"Chat message processing error: {e}")
            return {
                "success": False,
                "error": "Failed to process chat message",
                "details": str(e)
            }
    
    async def _process_text_message(
        self,
        user_id: str,
        message: str,
        context: Optional[Dict[str, Any]],
        user_profile: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process text message with LLM"""
        try:
            if not self.llm_service:
                return {
                    "success": False,
                    "error": "LLM service not available"
                }
            
            # Generate AI response
            llm_result = await self.llm_service.generate_chat_response(
                message=message,
                context=context,
                user_profile=user_profile
            )
            
            if not llm_result.get("success"):
                return llm_result
            
            # Add personalization info
            personalization_reason = ""
            if user_profile and user_profile.get("preferences"):
                personalization_reason = "Response personalized based on your preferences and shopping history"
            
            return {
                "success": True,
                "response": llm_result.get("response", ""),
                "personalized": llm_result.get("personalized", False),
                "context_used": llm_result.get("context_used", False),
                "personalization_reason": personalization_reason
            }
            
        except Exception as e:
            logger.error(f"Text message processing error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _process_image_message(
        self,
        user_id: str,
        message: str,
        image_data: str,
        context: Optional[Dict[str, Any]],
        user_profile: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process image message with vision AI"""
        try:
            if not self.image_service or not self.llm_service:
                return {
                    "success": False,
                    "error": "Image or LLM service not available"
                }
            
            # Process image upload
            upload_result = await self.image_service.process_image_upload(image_data)
            if not upload_result.get("success"):
                return upload_result
            
            # Analyze image with AI
            analysis_result = await self.llm_service.analyze_image(image_data)
            if not analysis_result.get("success"):
                return analysis_result
            
            # Generate contextual response
            combined_prompt = f"{message}\n\nImage analysis: {analysis_result.get('description', '')}"
            
            llm_result = await self.llm_service.generate_chat_response(
                message=combined_prompt,
                context=context,
                user_profile=user_profile
            )
            
            if not llm_result.get("success"):
                return llm_result
            
            return {
                "success": True,
                "response": llm_result.get("response", ""),
                "image_url": upload_result.get("image_url"),
                "image_analysis": analysis_result.get("description"),
                "personalized": llm_result.get("personalized", False),
                "context_used": llm_result.get("context_used", False)
            }
            
        except Exception as e:
            logger.error(f"Image message processing error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_conversation_context(
        self,
        user_id: str,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get conversation context for AI"""
        try:
            # Try cache first
            if self.redis_service:
                cached_context = await self.redis_service.get_user_context(user_id)
                if cached_context:
                    return cached_context
            
            # Get from conversation service
            if self.conversation_service:
                history_result = await self.conversation_service.get_conversation_history(
                    user_id, conversation_id, limit=10
                )
                
                if history_result.get("success"):
                    messages = history_result.get("messages", [])
                    context = {
                        "recent_messages": messages,
                        "conversation_id": conversation_id,
                        "message_count": len(messages)
                    }
                    
                    # Cache context
                    if self.redis_service:
                        await self.redis_service.cache_user_context(user_id, context)
                    
                    return context
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return None
    
    async def _update_conversation_cache(
        self,
        user_id: str,
        conversation_id: str,
        user_message_id: str,
        assistant_message_id: str,
        user_message: str,
        assistant_message: str
    ) -> None:
        """Update conversation cache with new messages"""
        try:
            if not self.redis_service:
                return
            
            # Get existing cache
            cached_conv = await self.redis_service.get_cached_conversation(user_id, conversation_id)
            
            if cached_conv:
                messages = cached_conv.get("messages", [])
            else:
                messages = []
            
            # Add new messages
            messages.extend([
                {
                    "message_id": user_message_id,
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "message_id": assistant_message_id,
                    "role": "assistant",
                    "content": assistant_message,
                    "timestamp": datetime.now().isoformat()
                }
            ])
            
            # Keep only recent messages
            messages = messages[-20:]  # Keep last 20 messages
            
            # Update cache
            await self.redis_service.cache_conversation(
                user_id, conversation_id, messages
            )
            
        except Exception as e:
            logger.error(f"Error updating conversation cache: {e}")
    
    async def get_chat_suggestions(
        self,
        user_id: str,
        context: Optional[str] = None
    ) -> List[str]:
        """Get chat suggestions for user"""
        try:
            # Default suggestions
            suggestions = [
                "Show me trending products",
                "Find deals under $50",
                "What's new in electronics?",
                "Help me find a gift",
                "Search for organic food"
            ]
            
            # Personalize based on user profile
            if self.user_service:
                profile_result = await self.user_service.get_user_profile(user_id)
                if profile_result.get("success"):
                    user_profile = profile_result.get("data", {})
                    preferences = user_profile.get("preferences", {})
                    
                    # Customize suggestions based on preferences
                    if preferences.get("category") == "Electronics":
                        suggestions.insert(0, "Show me the latest smartphones")
                    elif preferences.get("category") == "Groceries":
                        suggestions.insert(0, "Find healthy snack options")
            
            return suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logger.error(f"Error getting chat suggestions: {e}")
            return [
                "How can I help you today?",
                "What are you looking for?",
                "Show me popular products"
            ]