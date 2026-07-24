"""
Chat Orchestrator - Layer 2: Orchestration
Coordinates chat workflow with enhanced image intelligence and function calling
"""
import asyncio
from typing import Any, Dict, List, Optional

from app.addons.image.processor import ImageProcessor
from app.addons.memory.short_term import ShortTermMemory
from app.domain.conversations.service import ConversationService
from app.domain.users.service import UserService
from app.intelligence.engine import LLMEngine
from app.intelligence.tools.image_tools import ImageTools
from app.intelligence.tools.product_tools import ProductTools
from app.intelligence.tools.user_tools import UserTools
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
        """Register only the three approved tools with LLM"""
        if not self.llm:
            return
            
        # Clear any existing tools in self.llm.tools
        self.llm.tools.clear()
        
        # 1. Register search_products
        self.llm.register_tool(
            'search_products',
            self._tool_search_products,
            'Search the product catalog. Returns matching products as a list.',
            {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string', 'description': 'Search query'},
                    'category': {'type': 'string', 'description': 'Optional category filter'},
                    'limit': {'type': 'integer', 'default': 5}
                },
                'required': ['query']
            }
        )
        
        # 2. Register get_variants
        self.llm.register_tool(
            'get_variants',
            self._tool_get_variants,
            'Find strict variants of a product (same product, differing only in size or color).',
            {
                'type': 'object',
                'properties': {
                    'product_id': {'type': 'string', 'description': 'The product ID'}
                },
                'required': ['product_id']
            }
        )
        
        # 3. Register get_user_preferences
        self.llm.register_tool(
            'get_user_preferences',
            self._tool_get_user_preferences,
            "Retrieve the current user's shopping preferences for personalization. Strips PII.",
            {
                'type': 'object',
                'properties': {}
            }
        )

    def set_variant_tools(self, tools: Any):
        self.variant_tools = tools
        
    def set_personalization_tools(self, tools: Any):
        self.personalization_tools = tools
        
    def set_workflow_tools(self, tools: Any):
        self.workflow_tools = tools

    async def _tool_search_products(self, query: str, category: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search products scoped by the active tenant"""
        from app.container import get_container
        from app.core.security.context import tenant_context_var, user_id_var
        
        tenant = tenant_context_var.get()
        user_id = user_id_var.get() or "guest"
        
        container = get_container()
        search_orchestrator = container.get("search_orchestrator")
        if not search_orchestrator:
            return [{"error": "Search service not available"}]
            
        result = await search_orchestrator.handle(
            query=query,
            user_id=user_id,
            filters={"category": category} if category else {},
            limit=limit,
            tenant_context=tenant
        )
        
        products = result.get("results", [])
        return [
            {
                'id': p.get('id'),
                'title': p.get('title'),
                'price': p.get('price', {}).get('selling') or p.get('selling_price'),
                'category': p.get('category'),
                'brand': p.get('brand'),
                'rating': p.get('rating'),
                'description': p.get('description'),
                'url': p.get('url'),
                'selling_price': p.get('selling_price'),
                'stock': p.get('stock'),
                'online_available': p.get('online_available'),
                'breakdown': p.get('breakdown'),
            }
            for p in products
        ]

    async def _tool_get_variants(self, product_id: str) -> List[Dict[str, Any]]:
        """Get product variants scoped by active tenant collection"""
        from app.core.security.context import tenant_context_var
        tenant = tenant_context_var.get()
        
        if not self.variant_tools:
            return [{"error": "Variant service not available"}]
            
        # Get variants from service
        collection = tenant.collection_name if tenant else "products"
        
        # Call the underlying hybrid search find_strict_variants
        variants = await self.variant_tools.hybrid_search.find_strict_variants(
            product_id=product_id,
            user_preferences={},
            limit=10,
            collection=collection
        )
        
        return [
            {
                'id': p.get('id'),
                'title': p.get('title'),
                'price': p.get('price', {}).get('selling') or p.get('selling_price'),
                'brand': p.get('brand'),
                'size': p.get('size'),
                'color': p.get('color'),
                'stock': p.get('stock')
            }
            for p in variants
        ]

    async def _tool_get_user_preferences(self) -> Dict[str, Any]:
        """Get user preferences and explicitly strip PII"""
        from app.core.security.context import tenant_context_var, user_id_var
        user_id = user_id_var.get()
        tenant = tenant_context_var.get()
        if not user_id or not tenant:
            return {}
            
        profile = await self.users.get_user_profile(tenant.organization_id, user_id)
        if not profile:
            return {}
            
        prefs = profile.get('preferences', {})
        # Strip PII — only return category/brand/price preferences
        safe_prefs = {
            "favorite_categories": prefs.get("favorite_categories", []) or prefs.get("categories", []),
            "preferred_brands": prefs.get("preferred_brands", []) or prefs.get("brands", []),
            "price_range": prefs.get("price_range", {}),
            "min_rating": prefs.get("min_rating", 3.0),
        }
        return safe_prefs

    async def handle_completion(
        self, request: Any, tenant_context: Optional[Any] = None, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle OpenAI-style chat completion request"""
        try:
            user_id = user_id or request.user_id
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
                image_data=request.image_data,
                tenant_context=tenant_context
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            return {"success": False, "error": str(e)}

    async def stream_completion(
        self, request: Any, tenant_context: Optional[Any] = None, user_id: Optional[str] = None
    ):
        """Stream the same catalog-grounded answer used by non-streaming chat."""
        try:
            import json

            result = await self.handle_completion(request, tenant_context, user_id=user_id)
            if not result.get("success"):
                yield f"data: {json.dumps({'error': result.get('error', 'Chat failed')})}\n\n"
                yield "data: [DONE]\n\n"
                return

            for chunk in result.get("response", "").split():
                data = json.dumps({"choices": [{"delta": {"content": chunk + " "}}]})
                yield f"data: {data}\n\n"
                
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

    async def process_chat_message(self, *args, **kwargs) -> Dict[str, Any]:
        """Alias for WebSocket handlers compatibility"""
        return await self.handle(*args, **kwargs)

    async def handle(
        self, 
        message: str, 
        user_id: str, 
        conversation_id: str,
        message_type: str = 'text',
        image_data: Optional[str] = None,
        tenant_context: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Handle chat message with enhanced image intelligence and function calling"""
        try:
            from app.core.security.context import tenant_context_var, user_id_var
            from app.core.security.input_sanitizer import sanitize_user_input
            
            tenant_context_var.set(tenant_context)
            user_id_var.set(user_id)
            if not tenant_context:
                return {"success": False, "error": "Tenant context required"}
            organization_id = tenant_context.organization_id
            
            # Apply input sanitizer
            sanitized_message, is_suspicious = sanitize_user_input(message)
            if is_suspicious:
                return {
                    "success": True,
                    "response": sanitized_message,
                    "conversation_id": conversation_id,
                    "message_id": "blocked",
                    "function_called": None,
                    "image_analysis": None,
                    "features_used": {
                        "blocked": True,
                        "reason": "input_sanitization"
                    }
                }
            
            logger.info(f"🎯 Processing {message_type} message for user {user_id}")
            
            # CRITICAL: Ensure conversation exists before saving messages
            conversation = await self.conversations.get_conversation(organization_id, conversation_id)
            if not conversation:
                # Create conversation if it doesn't exist
                actual_conversation_id = await self.conversations.create_conversation(
                    organization_id, user_id, "New Chat", channel="rest"
                )
                conversation_id = actual_conversation_id
            elif conversation.get('user_id') != user_id:
                # User doesn't own this conversation
                raise Exception(f"Access denied to conversation {conversation_id}")
            
            # Get user context for personalization
            context = await self._build_user_context(organization_id, user_id, conversation_id)
            
            # Enhanced image handling with new intelligence capabilities
            image_analysis = None
            enhanced_message = sanitized_message
            
            if message_type == 'image' and image_data and self.image_tools:
                logger.info("🖼️ Processing image with enhanced intelligence")
                
                # Use enhanced image analysis
                image_result = await self.image_tools.analyze_product_image(
                    image_data, 
                    organization_id,
                    user_id,
                    context.get('user_preferences', {})
                )
                
                if image_result.get('success'):
                    image_analysis = image_result
                    
                    # Build enhanced message with analysis results
                    enhanced_message = self._build_enhanced_image_message(sanitized_message, image_result)
                    
                    logger.info(f"✅ Enhanced image analysis completed: {image_result.get('analysis_type')}")
                else:
                    logger.warning(f"⚠️ Image analysis failed: {image_result.get('error')}")
                    # Fallback to basic image processing
                    if self.image_processor:
                        upload_result = await self.image_processor.upload_image(
                            image_data, organization_id, user_id
                        )
                        if upload_result.get('success'):
                            basic_analysis = await self.llm.analyze_image(image_data)
                            if basic_analysis:
                                enhanced_message = f"{sanitized_message}\n\nImage analysis: {basic_analysis}"
            
            # Generate response with function calling
            result = await self.llm.generate_with_tools(enhanced_message, context, tenant_context)
            
            if not result.get('success'):
                return {"success": False, "error": result.get('error', 'Failed to generate response')}
            
            response_text = result.get('response', '')
            
            # Save user message with enhanced metadata
            await self.conversations.save_message(
                organization_id, conversation_id, user_id, message, role='user',
                metadata={
                    'type': message_type, 
                    'image_analysis': image_analysis,
                    'enhanced_processing': bool(image_analysis)
                }
            )
            
            # Save assistant message
            assistant_message_id = await self.conversations.save_message(
                organization_id, conversation_id, user_id, response_text, role='assistant',
                metadata={
                    'function_called': result.get('function_called'),
                    'function_result': result.get('function_result'),
                    'image_intelligence_used': bool(image_analysis)
                }
            )
            
            # Update context cache
            await self._update_context_cache(organization_id, user_id, context, message, response_text)
            
            return {
                "success": True,
                "response": response_text,
                "conversation_id": conversation_id,
                "message_id": assistant_message_id,
                "function_called": result.get('function_called'),
                "citations": result.get("citations", []),
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
    
    async def _build_user_context(
        self, organization_id: str, user_id: str, conversation_id: str
    ) -> Dict[str, Any]:
        """Build comprehensive user context for personalization"""
        context = await self.memory.get_context(organization_id, user_id)
        if not context:
            # Build context from user profile and conversation
            profile = await self.users.get_user_profile(organization_id, user_id)
            messages = await self.conversations.get_messages(organization_id, conversation_id, limit=5)
            
            context = {
                'user_preferences': profile.get('preferences') if profile else {},
                'user_behavior': profile.get('behavior') if profile else {},
                'recent_messages': messages
            }
            
            # Cache context
            await self.memory.save_context(organization_id, user_id, context)
        
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
    
    async def _update_context_cache(
        self,
        organization_id: str,
        user_id: str,
        context: Dict[str, Any],
        user_message: str,
        assistant_response: str,
    ):
        """Update context cache with new conversation data"""
        if context:
            context['recent_messages'].append({'role': 'user', 'message': user_message})
            context['recent_messages'].append({'role': 'assistant', 'message': assistant_response})
            
            # Keep only last 10 messages for context
            if len(context['recent_messages']) > 10:
                context['recent_messages'] = context['recent_messages'][-10:]
            
            await self.memory.save_context(organization_id, user_id, context)
