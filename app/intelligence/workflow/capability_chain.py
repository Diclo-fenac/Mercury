"""
Capability Chain - Layer 3: Intelligence
Autonomous capability chaining for intelligent workflow orchestration
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from app.utils.logger import get_logger

logger = get_logger("capability_chain")


class CapabilityType(Enum):
    """Types of capabilities that can be chained"""
    IMAGE_ANALYSIS = "image_analysis"
    BARCODE_DETECTION = "barcode_detection"
    PRODUCT_SEARCH = "product_search"
    VARIANT_DISCOVERY = "variant_discovery"
    PERSONALIZATION = "personalization"
    AVAILABILITY_CHECK = "availability_check"
    SUBSTITUTE_SUGGESTION = "substitute_suggestion"


@dataclass
class CapabilityResult:
    """Result from a capability execution"""
    capability: CapabilityType
    success: bool
    data: Dict[str, Any]
    confidence: float
    execution_time_ms: int
    next_suggestions: List[CapabilityType]


class CapabilityChain:
    """Autonomous capability chaining orchestrator"""
    
    def __init__(self):
        # Define capability dependencies and flow patterns
        self.CAPABILITY_FLOWS = {
            # Image-driven workflows
            CapabilityType.IMAGE_ANALYSIS: {
                'triggers': [CapabilityType.BARCODE_DETECTION, CapabilityType.PRODUCT_SEARCH],
                'confidence_threshold': 0.7,
                'autonomous': True
            },
            CapabilityType.BARCODE_DETECTION: {
                'triggers': [CapabilityType.PRODUCT_SEARCH, CapabilityType.AVAILABILITY_CHECK],
                'confidence_threshold': 0.9,  # High confidence for barcode
                'autonomous': True
            },
            
            # Search-driven workflows
            CapabilityType.PRODUCT_SEARCH: {
                'triggers': [CapabilityType.VARIANT_DISCOVERY, CapabilityType.PERSONALIZATION],
                'confidence_threshold': 0.6,
                'autonomous': True
            },
            CapabilityType.VARIANT_DISCOVERY: {
                'triggers': [CapabilityType.AVAILABILITY_CHECK, CapabilityType.PERSONALIZATION],
                'confidence_threshold': 0.8,
                'autonomous': True
            },
            
            # Personalization workflows
            CapabilityType.PERSONALIZATION: {
                'triggers': [CapabilityType.SUBSTITUTE_SUGGESTION],
                'confidence_threshold': 0.5,
                'autonomous': True
            },
            
            # User-triggered workflows
            CapabilityType.SUBSTITUTE_SUGGESTION: {
                'triggers': [],
                'confidence_threshold': 0.7,
                'autonomous': False  # Requires user confirmation
            },
            CapabilityType.AVAILABILITY_CHECK: {
                'triggers': [CapabilityType.SUBSTITUTE_SUGGESTION],
                'confidence_threshold': 0.8,
                'autonomous': True
            }
        }
        
        # Execution history for learning
        self.execution_history: List[Dict[str, Any]] = []
    
    async def execute_chain(
        self,
        initial_capability: CapabilityType,
        context: Dict[str, Any],
        capability_handlers: Dict[CapabilityType, callable],
        max_chain_length: int = 5
    ) -> Dict[str, Any]:
        """
        Execute autonomous capability chain
        
        Args:
            initial_capability: Starting capability
            context: Execution context (user_id, session_id, etc.)
            capability_handlers: Map of capability types to handler functions
            max_chain_length: Maximum number of capabilities to chain
        """
        try:
            logger.info(f"🔗 Starting capability chain with {initial_capability.value}")
            
            chain_results = []
            current_capability = initial_capability
            chain_length = 0
            
            while current_capability and chain_length < max_chain_length:
                # Execute current capability
                result = await self._execute_capability(
                    current_capability, 
                    context, 
                    capability_handlers,
                    chain_results
                )
                
                chain_results.append(result)
                chain_length += 1
                
                # Determine next capability
                next_capability = await self._determine_next_capability(
                    result, 
                    context,
                    chain_results
                )
                
                if not next_capability:
                    logger.info(f"🏁 Chain completed after {chain_length} capabilities")
                    break
                
                current_capability = next_capability
                logger.info(f"⚡ Chaining to {current_capability.value}")
            
            # Build comprehensive result
            chain_summary = self._build_chain_summary(chain_results, context)
            
            # Record execution for learning
            self._record_execution(initial_capability, chain_results, context)
            
            return {
                "success": True,
                "initial_capability": initial_capability.value,
                "chain_length": chain_length,
                "capabilities_executed": [r.capability.value for r in chain_results],
                "results": [self._serialize_result(r) for r in chain_results],
                "summary": chain_summary,
                "autonomous_execution": True,
                "user_confirmations_needed": self._get_user_confirmations(chain_results)
            }
            
        except Exception as e:
            logger.error(f"❌ Capability chain execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "initial_capability": initial_capability.value,
                "partial_results": [self._serialize_result(r) for r in chain_results] if 'chain_results' in locals() else []
            }
    
    async def _execute_capability(
        self,
        capability: CapabilityType,
        context: Dict[str, Any],
        handlers: Dict[CapabilityType, callable],
        previous_results: List[CapabilityResult]
    ) -> CapabilityResult:
        """Execute a single capability"""
        import time
        start_time = time.time()
        
        try:
            handler = handlers.get(capability)
            if not handler:
                raise Exception(f"No handler found for capability {capability.value}")
            
            # Build capability-specific context
            capability_context = self._build_capability_context(
                capability, 
                context, 
                previous_results
            )
            
            # Execute capability
            logger.info(f"⚡ Executing {capability.value}")
            result_data = await handler(capability_context)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Determine confidence and next suggestions
            confidence = self._calculate_confidence(capability, result_data)
            next_suggestions = self._suggest_next_capabilities(capability, result_data, confidence)
            
            return CapabilityResult(
                capability=capability,
                success=result_data.get('success', False),
                data=result_data,
                confidence=confidence,
                execution_time_ms=execution_time,
                next_suggestions=next_suggestions
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            logger.error(f"❌ Capability {capability.value} failed: {e}")
            
            return CapabilityResult(
                capability=capability,
                success=False,
                data={"error": str(e)},
                confidence=0.0,
                execution_time_ms=execution_time,
                next_suggestions=[]
            )
    
    def _build_capability_context(
        self,
        capability: CapabilityType,
        base_context: Dict[str, Any],
        previous_results: List[CapabilityResult]
    ) -> Dict[str, Any]:
        """Build context for specific capability execution"""
        context = base_context.copy()
        
        # Add results from previous capabilities
        for result in previous_results:
            if result.success:
                context[f"{result.capability.value}_result"] = result.data
        
        # Add capability-specific context
        if capability == CapabilityType.VARIANT_DISCOVERY:
            # Need product information from search or barcode
            search_result = next((r for r in previous_results if r.capability == CapabilityType.PRODUCT_SEARCH), None)
            barcode_result = next((r for r in previous_results if r.capability == CapabilityType.BARCODE_DETECTION), None)
            
            if search_result and search_result.success:
                products = search_result.data.get('products', [])
                if products:
                    context['reference_product'] = products[0]
            elif barcode_result and barcode_result.success:
                context['reference_product'] = barcode_result.data.get('product_info', {})
        
        elif capability == CapabilityType.PERSONALIZATION:
            # Need products from search or variants
            products = []
            for result in previous_results:
                if result.success:
                    if result.capability == CapabilityType.PRODUCT_SEARCH:
                        products.extend(result.data.get('products', []))
                    elif result.capability == CapabilityType.VARIANT_DISCOVERY:
                        products.extend(result.data.get('variants', []))
            
            context['products_to_personalize'] = products
        
        return context
    
    def _calculate_confidence(self, capability: CapabilityType, result_data: Dict[str, Any]) -> float:
        """Calculate confidence score for capability result"""
        if not result_data.get('success'):
            return 0.0
        
        # Capability-specific confidence calculation
        if capability == CapabilityType.BARCODE_DETECTION:
            return 0.95 if result_data.get('barcode_detected') else 0.1
        
        elif capability == CapabilityType.IMAGE_ANALYSIS:
            analysis_confidence = result_data.get('analysis_confidence', 0.5)
            return min(analysis_confidence, 0.9)
        
        elif capability == CapabilityType.PRODUCT_SEARCH:
            products = result_data.get('products', [])
            if not products:
                return 0.1
            # Higher confidence with more results
            return min(0.8, 0.3 + (len(products) * 0.1))
        
        elif capability == CapabilityType.VARIANT_DISCOVERY:
            variants = result_data.get('variants', [])
            strict_matches = result_data.get('strict_matches', 0)
            if strict_matches > 0:
                return 0.9
            elif variants:
                return 0.6
            else:
                return 0.2
        
        elif capability == CapabilityType.PERSONALIZATION:
            personalized_count = result_data.get('products_processed', 0)
            return 0.7 if personalized_count > 0 else 0.3
        
        else:
            return 0.5  # Default confidence
    
    def _suggest_next_capabilities(
        self,
        current_capability: CapabilityType,
        result_data: Dict[str, Any],
        confidence: float
    ) -> List[CapabilityType]:
        """Suggest next capabilities based on current result"""
        flow_config = self.CAPABILITY_FLOWS.get(current_capability, {})
        base_triggers = flow_config.get('triggers', [])
        
        if confidence < flow_config.get('confidence_threshold', 0.5):
            return []  # Don't continue if confidence too low
        
        # Context-aware suggestions
        suggestions = []
        
        for trigger in base_triggers:
            # Add logic to determine if trigger is relevant
            if self._is_trigger_relevant(current_capability, trigger, result_data):
                suggestions.append(trigger)
        
        return suggestions
    
    def _is_trigger_relevant(
        self,
        current: CapabilityType,
        trigger: CapabilityType,
        result_data: Dict[str, Any]
    ) -> bool:
        """Determine if a trigger capability is relevant"""
        # Image analysis → barcode detection
        if current == CapabilityType.IMAGE_ANALYSIS and trigger == CapabilityType.BARCODE_DETECTION:
            return result_data.get('barcode_candidates', False)
        
        # Barcode → product search
        if current == CapabilityType.BARCODE_DETECTION and trigger == CapabilityType.PRODUCT_SEARCH:
            return result_data.get('barcode_detected', False)
        
        # Product search → variants
        if current == CapabilityType.PRODUCT_SEARCH and trigger == CapabilityType.VARIANT_DISCOVERY:
            products = result_data.get('products', [])
            return len(products) > 0
        
        # Search/variants → personalization
        if trigger == CapabilityType.PERSONALIZATION:
            return True  # Always relevant if we have products
        
        # Variants → availability
        if current == CapabilityType.VARIANT_DISCOVERY and trigger == CapabilityType.AVAILABILITY_CHECK:
            variants = result_data.get('variants', [])
            return len(variants) > 0
        
        return True  # Default to relevant
    
    async def _determine_next_capability(
        self,
        current_result: CapabilityResult,
        context: Dict[str, Any],
        chain_results: List[CapabilityResult]
    ) -> Optional[CapabilityType]:
        """Determine the next capability to execute"""
        if not current_result.success:
            logger.info(f"⏹️ Stopping chain due to failed capability: {current_result.capability.value}")
            return None
        
        # Check if we've already executed suggested capabilities
        executed_capabilities = {r.capability for r in chain_results}
        available_suggestions = [
            cap for cap in current_result.next_suggestions 
            if cap not in executed_capabilities
        ]
        
        if not available_suggestions:
            return None
        
        # Prioritize based on context and user preferences
        next_capability = self._prioritize_next_capability(
            available_suggestions,
            context,
            chain_results
        )
        
        return next_capability
    
    def _prioritize_next_capability(
        self,
        suggestions: List[CapabilityType],
        context: Dict[str, Any],
        chain_results: List[CapabilityResult]
    ) -> Optional[CapabilityType]:
        """Prioritize next capability based on context"""
        if not suggestions:
            return None
        
        # Priority order based on user value
        priority_order = [
            CapabilityType.PERSONALIZATION,      # Always valuable
            CapabilityType.VARIANT_DISCOVERY,    # High value for alternatives
            CapabilityType.AVAILABILITY_CHECK,   # Important for purchase decisions
            CapabilityType.PRODUCT_SEARCH,       # Fallback search
            CapabilityType.BARCODE_DETECTION,    # Specific use case
            CapabilityType.SUBSTITUTE_SUGGESTION  # User-triggered only
        ]
        
        # Find highest priority suggestion
        for priority_cap in priority_order:
            if priority_cap in suggestions:
                # Check if it's autonomous or needs user confirmation
                flow_config = self.CAPABILITY_FLOWS.get(priority_cap, {})
                if flow_config.get('autonomous', True):
                    return priority_cap
                else:
                    # Non-autonomous capabilities need user confirmation
                    logger.info(f"⏸️ {priority_cap.value} requires user confirmation")
                    continue
        
        return None
    
    def _build_chain_summary(
        self,
        chain_results: List[CapabilityResult],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build comprehensive summary of chain execution"""
        successful_capabilities = [r for r in chain_results if r.success]
        total_execution_time = sum(r.execution_time_ms for r in chain_results)
        
        # Extract key insights
        insights = {
            "workflow_completed": len(successful_capabilities) > 0,
            "capabilities_succeeded": len(successful_capabilities),
            "total_capabilities": len(chain_results),
            "total_execution_time_ms": total_execution_time,
            "average_confidence": sum(r.confidence for r in successful_capabilities) / len(successful_capabilities) if successful_capabilities else 0.0
        }
        
        # Extract business value
        business_value = self._calculate_business_value(successful_capabilities)
        insights.update(business_value)
        
        return insights
    
    def _calculate_business_value(self, successful_results: List[CapabilityResult]) -> Dict[str, Any]:
        """Calculate business value from successful capabilities"""
        value = {
            "image_intelligence_used": False,
            "product_discovery_enhanced": False,
            "personalization_applied": False,
            "variant_options_provided": False,
            "user_experience_score": 0.0
        }
        
        for result in successful_results:
            if result.capability == CapabilityType.IMAGE_ANALYSIS:
                value["image_intelligence_used"] = True
                value["user_experience_score"] += 0.2
            
            elif result.capability == CapabilityType.BARCODE_DETECTION:
                value["product_discovery_enhanced"] = True
                value["user_experience_score"] += 0.3
            
            elif result.capability == CapabilityType.PERSONALIZATION:
                value["personalization_applied"] = True
                value["user_experience_score"] += 0.25
            
            elif result.capability == CapabilityType.VARIANT_DISCOVERY:
                variants = result.data.get('variants', [])
                if variants:
                    value["variant_options_provided"] = True
                    value["user_experience_score"] += 0.2
        
        value["user_experience_score"] = min(1.0, value["user_experience_score"])
        return value
    
    def _get_user_confirmations(self, chain_results: List[CapabilityResult]) -> List[Dict[str, Any]]:
        """Get list of capabilities that need user confirmation"""
        confirmations = []
        
        for result in chain_results:
            if result.success:
                flow_config = self.CAPABILITY_FLOWS.get(result.capability, {})
                if not flow_config.get('autonomous', True):
                    confirmations.append({
                        "capability": result.capability.value,
                        "message": self._get_confirmation_message(result),
                        "data": result.data
                    })
        
        return confirmations
    
    def _get_confirmation_message(self, result: CapabilityResult) -> str:
        """Get user-friendly confirmation message"""
        if result.capability == CapabilityType.SUBSTITUTE_SUGGESTION:
            substitutes = result.data.get('substitutes', [])
            return f"I found {len(substitutes)} alternative products. Would you like to see them?"
        
        return f"Would you like to proceed with {result.capability.value}?"
    
    def _serialize_result(self, result: CapabilityResult) -> Dict[str, Any]:
        """Serialize capability result for JSON response"""
        return {
            "capability": result.capability.value,
            "success": result.success,
            "data": result.data,
            "confidence": result.confidence,
            "execution_time_ms": result.execution_time_ms,
            "next_suggestions": [cap.value for cap in result.next_suggestions]
        }
    
    def _record_execution(
        self,
        initial_capability: CapabilityType,
        chain_results: List[CapabilityResult],
        context: Dict[str, Any]
    ):
        """Record execution for learning and optimization"""
        execution_record = {
            "timestamp": context.get('timestamp'),
            "user_id": context.get('user_id'),
            "initial_capability": initial_capability.value,
            "chain_length": len(chain_results),
            "success_rate": len([r for r in chain_results if r.success]) / len(chain_results) if chain_results else 0,
            "total_time_ms": sum(r.execution_time_ms for r in chain_results),
            "capabilities_executed": [r.capability.value for r in chain_results]
        }
        
        self.execution_history.append(execution_record)
        
        # Keep only last 100 executions for memory management
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
        
        logger.info(f"📊 Recorded execution: {execution_record}")