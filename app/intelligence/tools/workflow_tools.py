"""
Workflow Tools - Layer 3: Intelligence
Function calling tools for autonomous capability chaining and workflow orchestration
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.intelligence.workflow.capability_chain import CapabilityChain, CapabilityType
from app.utils.logger import get_logger

logger = get_logger("workflow_tools")


class WorkflowTools:
    """Autonomous workflow orchestration tools for LLM function calling"""
    
    def __init__(
        self,
        capability_chain: CapabilityChain,
        image_tools=None,
        variant_tools=None,
        personalization_tools=None,
        product_tools=None
    ):
        self.capability_chain = capability_chain
        self.image_tools = image_tools
        self.variant_tools = variant_tools
        self.personalization_tools = personalization_tools
        self.product_tools = product_tools
        
        # Build capability handler mapping
        self.capability_handlers = self._build_capability_handlers()
    
    def _build_capability_handlers(self) -> Dict[CapabilityType, callable]:
        """Build mapping of capability types to handler functions"""
        handlers = {}
        
        # Image capabilities
        if self.image_tools:
            handlers[CapabilityType.IMAGE_ANALYSIS] = self._handle_image_analysis
            handlers[CapabilityType.BARCODE_DETECTION] = self._handle_barcode_detection
        
        # Product capabilities
        if self.product_tools:
            handlers[CapabilityType.PRODUCT_SEARCH] = self._handle_product_search
        
        # Variant capabilities
        if self.variant_tools:
            handlers[CapabilityType.VARIANT_DISCOVERY] = self._handle_variant_discovery
            handlers[CapabilityType.AVAILABILITY_CHECK] = self._handle_availability_check
            handlers[CapabilityType.SUBSTITUTE_SUGGESTION] = self._handle_substitute_suggestion
        
        # Personalization capabilities
        if self.personalization_tools:
            handlers[CapabilityType.PERSONALIZATION] = self._handle_personalization
        
        return handlers
    
    async def execute_autonomous_workflow(
        self,
        trigger_type: str,
        context: Dict[str, Any],
        max_chain_length: int = 5
    ) -> Dict[str, Any]:
        """
        Execute autonomous workflow based on trigger
        Automatically chains relevant capabilities
        """
        try:
            logger.info(f"🚀 Starting autonomous workflow: {trigger_type}")
            
            # Map trigger to initial capability
            initial_capability = self._map_trigger_to_capability(trigger_type)
            if not initial_capability:
                return {
                    "success": False,
                    "error": f"Unknown trigger type: {trigger_type}",
                    "trigger_type": trigger_type
                }
            
            # Add workflow metadata to context
            workflow_context = context.copy()
            workflow_context.update({
                "workflow_id": f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "trigger_type": trigger_type,
                "timestamp": datetime.now().isoformat(),
                "autonomous_execution": True
            })
            
            # Execute capability chain
            result = await self.capability_chain.execute_chain(
                initial_capability,
                workflow_context,
                self.capability_handlers,
                max_chain_length
            )
            
            if result.get('success'):
                # Generate user-friendly summary
                user_summary = self._generate_user_summary(result, trigger_type)
                result['user_summary'] = user_summary
                
                logger.info(f"✅ Autonomous workflow completed: {result.get('chain_length')} capabilities")
            else:
                logger.error(f"❌ Autonomous workflow failed: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Workflow execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "trigger_type": trigger_type,
                "autonomous_execution": True
            }
    
    async def suggest_next_actions(
        self,
        current_context: Dict[str, Any],
        user_intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Suggest proactive next actions based on current context
        Provides intelligent recommendations without executing
        """
        try:
            logger.info("🔮 Generating proactive action suggestions")
            
            suggestions = []
            
            # Analyze context for suggestion opportunities
            if current_context.get('image_data'):
                suggestions.append({
                    "action": "image_analysis",
                    "description": "Analyze the uploaded image for products and barcodes",
                    "confidence": 0.9,
                    "autonomous": True,
                    "expected_capabilities": ["image_analysis", "barcode_detection", "product_search"]
                })
            
            if current_context.get('search_query'):
                suggestions.append({
                    "action": "enhanced_search",
                    "description": "Search for products with variant discovery and personalization",
                    "confidence": 0.8,
                    "autonomous": True,
                    "expected_capabilities": ["product_search", "variant_discovery", "personalization"]
                })
            
            if current_context.get('product_id'):
                suggestions.append({
                    "action": "product_exploration",
                    "description": "Find variants and alternatives for this product",
                    "confidence": 0.85,
                    "autonomous": True,
                    "expected_capabilities": ["variant_discovery", "availability_check", "personalization"]
                })
            
            # Intent-based suggestions
            if user_intent:
                intent_suggestions = self._generate_intent_suggestions(user_intent, current_context)
                suggestions.extend(intent_suggestions)
            
            # Rank suggestions by relevance and confidence
            ranked_suggestions = sorted(suggestions, key=lambda x: x['confidence'], reverse=True)
            
            return {
                "success": True,
                "suggestions": ranked_suggestions[:3],  # Top 3 suggestions
                "context_analyzed": bool(current_context),
                "intent_considered": bool(user_intent),
                "proactive_intelligence": True
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating suggestions: {e}")
            return {
                "success": False,
                "error": str(e),
                "suggestions": []
            }
    
    async def get_workflow_status(
        self,
        workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get status of workflow execution
        Useful for monitoring and debugging
        """
        try:
            # Get recent execution history
            recent_executions = self.capability_chain.execution_history[-10:] if self.capability_chain.execution_history else []
            
            # Calculate performance metrics
            if recent_executions:
                avg_chain_length = sum(ex['chain_length'] for ex in recent_executions) / len(recent_executions)
                avg_success_rate = sum(ex['success_rate'] for ex in recent_executions) / len(recent_executions)
                avg_execution_time = sum(ex['total_time_ms'] for ex in recent_executions) / len(recent_executions)
            else:
                avg_chain_length = 0
                avg_success_rate = 0
                avg_execution_time = 0
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "recent_executions": len(recent_executions),
                "performance_metrics": {
                    "average_chain_length": round(avg_chain_length, 2),
                    "average_success_rate": round(avg_success_rate, 3),
                    "average_execution_time_ms": round(avg_execution_time, 0)
                },
                "available_capabilities": list(self.capability_handlers.keys()),
                "capability_flows_configured": len(self.capability_chain.CAPABILITY_FLOWS)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting workflow status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _map_trigger_to_capability(self, trigger_type: str) -> Optional[CapabilityType]:
        """Map trigger type to initial capability"""
        trigger_mapping = {
            "image_upload": CapabilityType.IMAGE_ANALYSIS,
            "barcode_scan": CapabilityType.BARCODE_DETECTION,
            "product_search": CapabilityType.PRODUCT_SEARCH,
            "find_variants": CapabilityType.VARIANT_DISCOVERY,
            "personalize_results": CapabilityType.PERSONALIZATION,
            "check_availability": CapabilityType.AVAILABILITY_CHECK
        }
        
        return trigger_mapping.get(trigger_type)
    
    def _generate_user_summary(self, workflow_result: Dict[str, Any], trigger_type: str) -> str:
        """Generate user-friendly summary of workflow execution"""
        if not workflow_result.get('success'):
            return f"Workflow failed: {workflow_result.get('error', 'Unknown error')}"
        
        capabilities = workflow_result.get('capabilities_executed', [])
        chain_length = workflow_result.get('chain_length', 0)
        summary = workflow_result.get('summary', {})
        
        # Build narrative summary
        parts = [f"Completed {chain_length} intelligent actions"]
        
        if 'image_analysis' in capabilities:
            parts.append("analyzed your image")
        
        if 'barcode_detection' in capabilities:
            parts.append("detected product barcode")
        
        if 'product_search' in capabilities:
            parts.append("found matching products")
        
        if 'variant_discovery' in capabilities:
            parts.append("discovered product variants")
        
        if 'personalization' in capabilities:
            parts.append("applied your preferences")
        
        # Add performance info
        total_time = summary.get('total_execution_time_ms', 0)
        if total_time > 0:
            parts.append(f"in {total_time}ms")
        
        # Add business value
        if summary.get('user_experience_score', 0) > 0.7:
            parts.append("with high relevance")
        
        return " → ".join(parts[:3]) + f" (and {len(parts)-3} more)" if len(parts) > 3 else " → ".join(parts)
    
    def _generate_intent_suggestions(self, user_intent: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate suggestions based on user intent"""
        suggestions = []
        intent_lower = user_intent.lower()
        
        if any(word in intent_lower for word in ['find', 'search', 'looking for']):
            suggestions.append({
                "action": "intelligent_search",
                "description": "Enhanced search with personalization and variant discovery",
                "confidence": 0.8,
                "autonomous": True,
                "expected_capabilities": ["product_search", "personalization", "variant_discovery"]
            })
        
        if any(word in intent_lower for word in ['similar', 'alternative', 'other options']):
            suggestions.append({
                "action": "find_alternatives",
                "description": "Find similar products and variants",
                "confidence": 0.85,
                "autonomous": True,
                "expected_capabilities": ["variant_discovery", "substitute_suggestion"]
            })
        
        if any(word in intent_lower for word in ['available', 'in stock', 'buy']):
            suggestions.append({
                "action": "check_purchase_options",
                "description": "Check availability and purchase options",
                "confidence": 0.9,
                "autonomous": True,
                "expected_capabilities": ["availability_check", "variant_discovery"]
            })
        
        return suggestions
    
    # Capability handler methods
    async def _handle_image_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle image analysis capability"""
        if not self.image_tools:
            return {"success": False, "error": "Image tools not available"}
        
        image_data = context.get('image_data')
        user_id = context.get('user_id')
        user_preferences = context.get('user_preferences', {})
        
        if not image_data:
            return {"success": False, "error": "No image data provided"}
        
        return await self.image_tools.analyze_product_image(image_data, user_id, user_preferences)
    
    async def _handle_barcode_detection(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle barcode detection capability"""
        if not self.image_tools:
            return {"success": False, "error": "Image tools not available"}
        
        image_data = context.get('image_data')
        user_id = context.get('user_id')
        
        if not image_data:
            return {"success": False, "error": "No image data provided"}
        
        return await self.image_tools.detect_barcode(image_data, user_id)
    
    async def _handle_product_search(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle product search capability"""
        if not self.product_tools:
            return {"success": False, "error": "Product tools not available"}
        
        # Extract search query from context or previous results
        query = context.get('search_query')
        if not query:
            # Try to extract from barcode result
            barcode_result = context.get('barcode_detection_result')
            if barcode_result and barcode_result.get('barcode_detected'):
                query = barcode_result['barcode_detected']['barcode_data']
        
        if not query:
            return {"success": False, "error": "No search query available"}
        
        # Call product search and ensure we return the result properly
        result = await self.product_tools.search_products(query, limit=10)
        
        # Ensure result has the expected structure
        if isinstance(result, list):
            # If result is a list of products, wrap it in proper structure
            return {
                "success": True,
                "products": result,
                "query": query,
                "total_results": len(result)
            }
        elif isinstance(result, dict):
            # If result is already a dict, ensure it has success flag
            if 'success' not in result:
                result['success'] = True
            return result
        else:
            return {"success": False, "error": "Unexpected result format from product search"}
    
    async def _handle_variant_discovery(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle variant discovery capability"""
        if not self.variant_tools:
            return {"success": False, "error": "Variant tools not available"}
        
        reference_product = context.get('reference_product')
        if not reference_product:
            return {"success": False, "error": "No reference product for variant discovery"}
        
        return await self.variant_tools.find_product_variants(reference_product)
    
    async def _handle_availability_check(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle availability check capability"""
        if not self.variant_tools:
            return {"success": False, "error": "Variant tools not available"}
        
        product_id = context.get('product_id')
        if not product_id:
            # Try to extract from reference product
            reference_product = context.get('reference_product')
            if reference_product:
                product_id = reference_product.get('id') or reference_product.get('pid')
        
        if not product_id:
            return {"success": False, "error": "No product ID for availability check"}
        
        return await self.variant_tools.check_product_availability(product_id)
    
    async def _handle_substitute_suggestion(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle substitute suggestion capability"""
        if not self.variant_tools:
            return {"success": False, "error": "Variant tools not available"}
        
        reference_product = context.get('reference_product')
        if not reference_product:
            return {"success": False, "error": "No reference product for substitute suggestions"}
        
        return await self.variant_tools.suggest_product_substitutes(reference_product)
    
    async def _handle_personalization(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle personalization capability"""
        if not self.personalization_tools:
            return {"success": False, "error": "Personalization tools not available"}
        
        user_id = context.get('user_id')
        session_id = context.get('session_id')
        products = context.get('products_to_personalize', [])
        
        if not user_id:
            return {"success": False, "error": "No user ID for personalization"}
        
        if not products:
            return {"success": False, "error": "No products to personalize"}
        
        return await self.personalization_tools.apply_behavioral_personalization(
            user_id, products, session_id
        )
    
    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions for LLM registration"""
        return {
            "execute_autonomous_workflow": {
                "description": "Execute autonomous workflow that chains multiple capabilities intelligently based on context",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "trigger_type": {
                            "type": "string",
                            "description": "Type of workflow trigger",
                            "enum": ["image_upload", "barcode_scan", "product_search", "find_variants", "personalize_results", "check_availability"]
                        },
                        "context": {
                            "type": "object",
                            "description": "Workflow execution context",
                            "properties": {
                                "user_id": {"type": "string"},
                                "session_id": {"type": "string"},
                                "image_data": {"type": "string"},
                                "search_query": {"type": "string"},
                                "product_id": {"type": "string"},
                                "user_preferences": {"type": "object"}
                            }
                        },
                        "max_chain_length": {
                            "type": "integer",
                            "description": "Maximum number of capabilities to chain",
                            "default": 5
                        }
                    },
                    "required": ["trigger_type", "context"]
                }
            },
            "suggest_next_actions": {
                "description": "Suggest proactive next actions based on current context and user intent",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "current_context": {
                            "type": "object",
                            "description": "Current conversation/interaction context"
                        },
                        "user_intent": {
                            "type": "string",
                            "description": "Optional user intent or query"
                        }
                    },
                    "required": ["current_context"]
                }
            },
            "get_workflow_status": {
                "description": "Get status and performance metrics of workflow execution system",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Optional specific workflow ID to check"
                        }
                    }
                }
            }
        }