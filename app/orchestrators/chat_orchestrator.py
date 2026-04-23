"""
Chat Orchestrator - Layer 2: Orchestration
Coordinates chat workflow with enhanced image intelligence and function calling
"""
from typing import Any, Dict, List, Optional, Union

from app.addons.image.processor import ImageProcessor
from app.addons.memory.short_term import ShortTermMemory
from app.domain.conversations.service import ConversationService
from app.domain.users.service import UserService
from app.intelligence.engine import LLMEngine
from app.intelligence.tools.image_tools import ImageTools
from app.intelligence.tools.personalization_tools import PersonalizationTools
from app.intelligence.tools.product_tools import ProductTools
from app.intelligence.tools.user_tools import UserTools
from app.intelligence.tools.variant_tools import VariantTools
from app.utils.logger import get_logger

logger = get_logger("chat_orchestrator")


class ChatOrchestrator:
    """Orchestrates chat workflow with enhanced AI and function calling"""
    
    def __init__(
        self,
        llm_engine: LLMEngine,
        memory: ShortTermMemory,
        user_service: UserService,
        conversation_service: ConversationService,
        image_processor: Optional[ImageProcessor],
        product_tools: ProductTools,
        user_tools: UserTools
    ):
        self.llm = llm_engine
        self.memory = memory
        self.users = user_service
        self.conversations = conversation_service
        self.image_processor = image_processor
        self.product_tools = product_tools
        self.user_tools = user_tools
        
        # Initialize image tools if image processor available
        self.image_tools = ImageTools(image_processor) if image_processor else None
        
        # Initialize variant tools (always available since HybridSearch is required)
        # Get hybrid_search from container - this will be injected properly in production
        self.variant_tools = None  # Will be set via dependency injection
        
        # Initialize personalization tools
        self.personalization_tools = None  # Will be set via dependency injection
        
        # Initialize workflow tools
        self.workflow_tools = None  # Will be set via dependency injection
        
        # Register tools with LLM
        self._register_tools()
    
    def _register_tools(self):
        """Register function calling tools with enhanced image intelligence"""
        # Product tools
        self.llm.register_tool(
            'search_products',
            self.product_tools.search_products,
            'Search for products by query and optional category',
            {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string', 'description': 'Search query'},
                    'category': {'type': 'string', 'description': 'Optional category'},
                    'limit': {'type': 'integer', 'default': 5}
                },
                'required': ['query']
            }
        )
        
        self.llm.register_tool(
            'get_product_details',
            self.product_tools.get_product_details,
            'Get detailed information about a specific product',
            {
                'type': 'object',
                'properties': {
                    'product_id': {'type': 'string', 'description': 'Product ID'}
                },
                'required': ['product_id']
            }
        )
        
        self.llm.register_tool(
            'get_trending',
            self.product_tools.get_trending,
            'Get trending products',
            {
                'type': 'object',
                'properties': {
                    'category': {'type': 'string', 'description': 'Optional category'},
                    'limit': {'type': 'integer', 'default': 5}
                }
            }
        )
        
        # User tools
        self.llm.register_tool(
            'get_user_preferences',
            self.user_tools.get_user_preferences,
            'Get user preferences and shopping history',
            {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'User ID'}
                },
                'required': ['user_id']
            }
        )
        
        # Enhanced image intelligence tools
        if self.image_tools:
            image_tool_definitions = self.image_tools.get_tool_definitions()
            
            self.llm.register_tool(
                'analyze_product_image',
                self.image_tools.analyze_product_image,
                image_tool_definitions['analyze_product_image']['description'],
                image_tool_definitions['analyze_product_image']['parameters']
            )
            
            self.llm.register_tool(
                'detect_barcode',
                self.image_tools.detect_barcode,
                image_tool_definitions['detect_barcode']['description'],
                image_tool_definitions['detect_barcode']['parameters']
            )
            
            self.llm.register_tool(
                'get_cached_analysis',
                self.image_tools.get_cached_analysis,
                image_tool_definitions['get_cached_analysis']['description'],
                image_tool_definitions['get_cached_analysis']['parameters']
            )
            
    def set_variant_tools(self, variant_tools: VariantTools):
        """Set variant tools (called by container during initialization)"""
        self.variant_tools = variant_tools
        # Re-register tools to include variant tools
        self._register_variant_tools()
    
    def set_personalization_tools(self, personalization_tools: PersonalizationTools):
        """Set personalization tools (called by container during initialization)"""
        self.personalization_tools = personalization_tools
        # Register personalization tools
        self._register_personalization_tools()
    
    def set_workflow_tools(self, workflow_tools):
        """Set workflow tools (called by container during initialization)"""
        self.workflow_tools = workflow_tools
        # Register workflow tools
        self._register_workflow_tools()
    
    def _register_variant_tools(self):
        """Register variant discovery tools"""
        if self.variant_tools:
            variant_tool_definitions = self.variant_tools.get_tool_definitions()
            
            self.llm.register_tool(
                'find_product_variants',
                self.variant_tools.find_product_variants,
                variant_tool_definitions['find_product_variants']['description'],
                variant_tool_definitions['find_product_variants']['parameters']
            )
            
            self.llm.register_tool(
                'suggest_product_substitutes',
                self.variant_tools.suggest_product_substitutes,
                variant_tool_definitions['suggest_product_substitutes']['description'],
                variant_tool_definitions['suggest_product_substitutes']['parameters']
            )
            
            self.llm.register_tool(
                'check_product_availability',
                self.variant_tools.check_product_availability,
                variant_tool_definitions['check_product_availability']['description'],
                variant_tool_definitions['check_product_availability']['parameters']
            )
            
            logger.info("✅ Variant discovery tools registered")
    
    def _register_personalization_tools(self):
        """Register behavioral personalization tools"""
        if self.personalization_tools:
            personalization_tool_definitions = self.personalization_tools.get_tool_definitions()
            
            self.llm.register_tool(
                'apply_behavioral_personalization',
                self.personalization_tools.apply_behavioral_personalization,
                personalization_tool_definitions['apply_behavioral_personalization']['description'],
                personalization_tool_definitions['apply_behavioral_personalization']['parameters']
            )
            
            self.llm.register_tool(
                'set_session_constraints',
                self.personalization_tools.set_session_constraints,
                personalization_tool_definitions['set_session_constraints']['description'],
                personalization_tool_definitions['set_session_constraints']['parameters']
            )
            
            self.llm.register_tool(
                'get_behavioral_context',
                self.personalization_tools.get_behavioral_context,
                personalization_tool_definitions['get_behavioral_context']['description'],
                personalization_tool_definitions['get_behavioral_context']['parameters']
            )
            
            logger.info("✅ Behavioral personalization tools registered")
    
    def _register_workflow_tools(self):
        """Register autonomous workflow orchestration tools"""
        if self.workflow_tools:
            workflow_tool_definitions = self.workflow_tools.get_tool_definitions()
            
            self.llm.register_tool(
                'execute_autonomous_workflow',
                self.workflow_tools.execute_autonomous_workflow,
                workflow_tool_definitions['execute_autonomous_workflow']['description'],
                workflow_tool_definitions['execute_autonomous_workflow']['parameters']
            )
            
            self.llm.register_tool(
                'suggest_next_actions',
                self.workflow_tools.suggest_next_actions,
                workflow_tool_definitions['suggest_next_actions']['description'],
                workflow_tool_definitions['suggest_next_actions']['parameters']
            )
            
            self.llm.register_tool(
                'get_workflow_status',
                self.workflow_tools.get_workflow_status,
                workflow_tool_definitions['get_workflow_status']['description'],
                workflow_tool_definitions['get_workflow_status']['parameters']
            )
            
            logger.info("✅ Autonomous workflow tools registered")
    
    async def handle_completion(self, request: Any) -> Dict[str, Any]:
        """Handle OpenAI-style chat completion request"""
        try:
            user_id = request.user_id
            conversation_id = request.conversation_id
            
            # Use last message as the primary query for existing handle logic
            # In a real upgrade, handle() would be refactored to support full message arrays
            last_message = request.messages[-1].content if request.messages else ""
            
            # Map request to existing handle logic
            # This maintains compatibility while we transition
            result = await self.handle(
                message=last_message,
                user_id=user_id,
                conversation_id=conversation_id,
                message_type='text',
                image_data=request.image_data
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            return {"success": False, "error": str(e)}

    async def stream_completion(self, request: Any):
        """Stream chat completion using SSE"""
        try:
            # Simple mock streaming for now
            # In production, this would use self.llm.generate_stream
            message = request.messages[-1].content if request.messages else ""
            
            # Just a placeholder for actual streaming logic
            full_text = f"Streaming response for: {message}"
            import asyncio
            import json
            
            for chunk in full_text.split():
                data = json.dumps({"choices": [{"delta": {"content": chunk + " "}}]})
                yield f"data: {data}\n\n"
                await asyncio.sleep(0.1)
                
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get definitions of all registered tools"""
        # This would return definitions from self.llm.tools
        return [
            {"name": name, "description": info["description"], "parameters": info["parameters"]}
            for name, info in self.llm.tools.items()
        ]

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any], user_id: str = None) -> Any:
        """Directly execute a registered tool"""
        if tool_name not in self.llm.tools:
            raise Exception(f"Tool {tool_name} not found")
        
        tool_info = self.llm.tools[tool_name]
        func = tool_info['function']
        
        # In a real app, you might need to inject user_id into parameters
        if asyncio.iscoroutinefunction(func):
            return await func(**parameters)
        return func(**parameters)

    async def handle(
        self, 
        message: str, 
        user_id: str, 
        conversation_id: str,
        message_type: str = 'text',
        image_data: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle chat message with enhanced image intelligence and function calling"""
        try:
            logger.info(f"🎯 Processing {message_type} message for user {user_id}")
            
            # CRITICAL: Ensure conversation exists before saving messages
            conversation = await self.conversations.get_conversation(conversation_id)
            if not conversation:
                # Create conversation if it doesn't exist
                actual_conversation_id = await self.conversations.create_conversation(user_id, "New Chat")
                conversation_id = actual_conversation_id
            elif conversation.get('user_id') != user_id:
                # User doesn't own this conversation
                raise Exception(f"Access denied to conversation {conversation_id}")
            
            # Get user context for personalization
            context = await self._build_user_context(user_id, conversation_id)
            
            # Enhanced image handling with new intelligence capabilities
            image_analysis = None
            enhanced_message = message
            
            if message_type == 'image' and image_data and self.image_tools:
                logger.info("🖼️ Processing image with enhanced intelligence")
                
                # Use enhanced image analysis
                image_result = await self.image_tools.analyze_product_image(
                    image_data, 
                    user_id,
                    context.get('user_preferences', {})
                )
                
                if image_result.get('success'):
                    image_analysis = image_result
                    
                    # Build enhanced message with analysis results
                    enhanced_message = self._build_enhanced_image_message(message, image_result)
                    
                    logger.info(f"✅ Enhanced image analysis completed: {image_result.get('analysis_type')}")
                else:
                    logger.warning(f"⚠️ Image analysis failed: {image_result.get('error')}")
                    # Fallback to basic image processing
                    if self.image_processor:
                        upload_result = await self.image_processor.upload_image(image_data, user_id)
                        if upload_result.get('success'):
                            basic_analysis = await self.llm.analyze_image(image_data)
                            if basic_analysis:
                                enhanced_message = f"{message}\n\nImage analysis: {basic_analysis}"
            
            # Generate response with function calling
            result = await self.llm.generate_with_tools(enhanced_message, context)
            
            if not result.get('success'):
                return {"success": False, "error": result.get('error', 'Failed to generate response')}
            
            response_text = result.get('response', '')
            
            # Save user message with enhanced metadata
            await self.conversations.save_message(
                conversation_id, user_id, message, role='user',
                metadata={
                    'type': message_type, 
                    'image_analysis': image_analysis,
                    'enhanced_processing': bool(image_analysis)
                }
            )
            
            # Save assistant message
            await self.conversations.save_message(
                conversation_id, user_id, response_text, role='assistant',
                metadata={
                    'function_called': result.get('function_called'),
                    'function_result': result.get('function_result'),
                    'image_intelligence_used': bool(image_analysis)
                }
            )
            
            # Update context cache
            await self._update_context_cache(user_id, context, message, response_text)
            
            return {
                "success": True,
                "response": response_text,
                "conversation_id": conversation_id,
                "function_called": result.get('function_called'),
                "image_analysis": image_analysis,
                "features_used": {
                    "function_calling": bool(result.get('function_called')),
                    "enhanced_image_analysis": bool(image_analysis and image_analysis.get('workflow_completed')),
                    "barcode_detection": bool(image_analysis and image_analysis.get('barcode_detected')),
                    "product_identification": bool(image_analysis and image_analysis.get('product_identified')),
                    "search_suggestions": bool(image_analysis and image_analysis.get('search_suggestions')),
                    "context_awareness": True,
                    "personalization": bool(context.get('user_preferences'))
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Chat handling error for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _build_user_context(self, user_id: str, conversation_id: str) -> Dict[str, Any]:
        """Build comprehensive user context for personalization"""
        context = await self.memory.get_context(user_id)
        if not context:
            # Build context from user profile and conversation
            profile = await self.users.get_user_profile(user_id)
            messages = await self.conversations.get_messages(conversation_id, limit=5)
            
            context = {
                'user_preferences': profile.get('preferences') if profile else {},
                'user_behavior': profile.get('behavior') if profile else {},
                'recent_messages': messages
            }
            
            # Cache context
            await self.memory.save_context(user_id, context)
        
        return context
    
    def _build_enhanced_image_message(self, original_message: str, image_analysis: Dict[str, Any]) -> str:
        """Build enhanced message with image analysis results"""
        parts = [original_message] if original_message.strip() else []
        
        # Add barcode information
        if image_analysis.get('barcode_detected'):
            barcode_info = image_analysis['barcode_detected']
            parts.append(f"Barcode detected: {barcode_info['barcode_data']} ({barcode_info['barcode_type']})")
        
        # Add product identification
        if image_analysis.get('product_identified'):
            product_info = image_analysis['product_identified']
            parts.append(f"Product identified: {product_info.get('description', 'Product detected')}")
            
            if product_info.get('category'):
                parts.append(f"Category: {product_info['category']}")
            if product_info.get('brand'):
                parts.append(f"Brand: {product_info['brand']}")
        
        # Add search suggestions context
        if image_analysis.get('search_suggestions'):
            suggestions = image_analysis['search_suggestions']
            if suggestions.get('exact_match'):
                parts.append("Exact product match available via barcode")
            elif suggestions.get('similar_products'):
                parts.append("Similar products can be found")
            elif suggestions.get('category_suggestions'):
                parts.append("Category browsing suggestions available")
        
        return "\n".join(parts)
    
    async def _update_context_cache(self, user_id: str, context: Dict[str, Any], user_message: str, assistant_response: str):
        """Update context cache with new conversation data"""
        if context:
            context['recent_messages'].append({'role': 'user', 'message': user_message})
            context['recent_messages'].append({'role': 'assistant', 'message': assistant_response})
            
            # Keep only last 10 messages for context
            if len(context['recent_messages']) > 10:
                context['recent_messages'] = context['recent_messages'][-10:]
            
            await self.memory.save_context(user_id, context)
