"""
Dependency Injection Container
Manages service lifecycle and dependencies
"""
import asyncio
from functools import lru_cache
from typing import Any, Dict

from app.settings import get_settings
from app.utils.logger import get_logger

logger = get_logger("container")


class Container:
    """
    Service container for dependency injection
    Follows clean architecture - no business logic here
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._initialized = False
        self.settings = get_settings()
    
    async def initialize(self) -> None:
        """Initialize all services in correct order"""
        if self._initialized:
            return
        
        logger.info("🔧 Initializing services...")
        
        # Layer 6: Infrastructure (DB, Cache, Storage)
        await self._init_infrastructure()
        
        # Layer 5: Domain Services (Business Logic)
        await self._init_domain_services()
        
        # Layer 4: Add-ons (Search, Memory, Personalization)
        await self._init_addons()
        
        # Layer 3: Intelligence (LLM Engine)
        await self._init_intelligence()
        
        # Layer 2: Orchestrators (Workflow)
        await self._init_orchestrators()
        
        self._initialized = True
        logger.info("✅ All services initialized")
    
    async def _init_infrastructure(self) -> None:
        """Initialize infrastructure layer"""
        from app.infrastructure.cache.redis import RedisClient
        from app.infrastructure.db.firestore import FirestoreClient
        from app.infrastructure.storage.gcs import GCSClient
        from app.infrastructure.vector.qdrant import QdrantClient
        
        # Redis - try to connect, continue if fails
        try:
            self._services['redis'] = RedisClient(
                host=self.settings.REDIS_HOST,
                port=self.settings.REDIS_PORT,
                db=self.settings.REDIS_DB,
                password=self.settings.REDIS_PASSWORD,
                url=self.settings.REDIS_URL
            )
            await asyncio.wait_for(self._services['redis'].connect(), timeout=5.0)
            logger.info("Redis connected")
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Redis not available: {e}")
            self._services['redis'] = None
        
        # Firestore - with timeout and fallback to mock in debug
        try:
            self._services['firestore'] = FirestoreClient(
                project_id=self.settings.GOOGLE_CLOUD_PROJECT,
                credentials_path=self.settings.FIREBASE_CREDENTIALS_PATH,
                collection_name=self.settings.FIRESTORE_COLLECTION
            )
            await asyncio.wait_for(self._services['firestore'].connect(), timeout=5.0)
            logger.info("Firestore connected")
        except (asyncio.TimeoutError, Exception) as e:
            logger.error(f"Firestore connection failed: {e}")
            if self.settings.DEBUG:
                logger.warning("⚠️ Falling back to MockFirestoreClient for local development")
                from app.infrastructure.db.mock_firestore import MockFirestoreClient
                self._services['firestore'] = MockFirestoreClient()
                await self._services['firestore'].connect()
            else:
                raise Exception(f"Firestore is required but failed to connect: {e}")
        
        # Qdrant - with timeout
        try:
            self._services['qdrant'] = QdrantClient(
                host=self.settings.QDRANT_HOST,
                port=self.settings.QDRANT_PORT,
                api_key=self.settings.QDRANT_API_KEY,
                collection_name=self.settings.QDRANT_COLLECTION_NAME
            )
            await asyncio.wait_for(self._services['qdrant'].connect(), timeout=5.0)
            logger.info("Qdrant connected")
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Qdrant not available: {e}")
            self._services['qdrant'] = None
        
        # GCS - with timeout
        try:
            self._services['gcs'] = GCSClient(
                bucket_name=self.settings.GCS_BUCKET_NAME,
                credentials_path=self.settings.GOOGLE_APPLICATION_CREDENTIALS
            )
            await asyncio.wait_for(self._services['gcs'].connect(), timeout=5.0)
            logger.info("GCS connected")
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"GCS not available: {e}")
            self._services['gcs'] = None
        
        logger.info("Infrastructure layer initialized")
    
    async def _init_domain_services(self) -> None:
        """Initialize domain services"""
        from app.domain.conversations.service import ConversationService
        from app.domain.pricing.service import PricingService
        from app.domain.products.service import ProductService
        from app.domain.products.trending_service import TrendingProductsService
        from app.domain.recommendations.engine import RecommendationEngine
        from app.domain.users.service import UserService
        
        # Product Service
        self._services['product_service'] = ProductService(
            firestore=self._services['firestore'],
            cache=self._services['redis']
        )
        
        # User Service
        self._services['user_service'] = UserService(
            firestore=self._services['firestore'],
            cache=self._services['redis']
        )
        
        # Pricing Service
        self._services['pricing_service'] = PricingService()
        
        # Trending Products Service
        self._services['trending_products_service'] = TrendingProductsService(
            cache=self._services['redis'],
            firestore=self._services['firestore']
        )
        
        # Recommendation Engine
        self._services['recommendation_engine'] = RecommendationEngine(
            product_service=self._services['product_service'],
            user_service=self._services['user_service']
        )
        
        # Conversation Service
        self._services['conversation_service'] = ConversationService(
            firestore=self._services['firestore'],
            cache=self._services['redis']
        )
        
        logger.info("Domain services initialized")
    
    async def _init_addons(self) -> None:
        """Initialize add-ons layer"""
        from app.addons.image.processor import ImageProcessor
        from app.addons.memory.short_term import ShortTermMemory
        from app.addons.personalization.scorer import PersonalizationScorer
        from app.addons.search.hybrid import HybridSearch
        
        # Search
        self._services['hybrid_search'] = HybridSearch(
            qdrant=self._services['qdrant'],
            firestore=self._services['firestore']
        )
        
        # Memory
        self._services['short_term_memory'] = ShortTermMemory(
            cache=self._services['redis']
        )
        
        # Personalization
        self._services['personalization_scorer'] = PersonalizationScorer(
            user_service=self._services['user_service'],
            cache=self._services['redis']
        )
        
        # Image Processor
        self._services['image_processor'] = ImageProcessor(
            storage=self._services['gcs'],
            cache=self._services['redis']
        )
        
        logger.info("Add-ons layer initialized")
    
    async def _init_intelligence(self) -> None:
        """Initialize intelligence layer"""
        from app.intelligence.engine import LLMEngine
        from app.intelligence.tools.product_tools import ProductTools
        from app.intelligence.tools.user_tools import UserTools
        
        # LLM Engine
        self._services['llm_engine'] = LLMEngine(
            api_key=self.settings.GOOGLE_API_KEY,
            project_id=self.settings.GOOGLE_CLOUD_PROJECT
        )
        await self._services['llm_engine'].initialize()
        
        # Tools (without SearchTools - will be created after orchestrators)
        self._services['product_tools'] = ProductTools(
            product_service=self._services['product_service']
        )
        
        self._services['user_tools'] = UserTools(
            user_service=self._services['user_service']
        )
        
        logger.info("✅ Intelligence layer initialized")
    
    async def _init_orchestrators(self) -> None:
        """Initialize orchestrators"""
        from app.orchestrators.chat_orchestrator import ChatOrchestrator
        from app.orchestrators.conversation_orchestrator import ConversationOrchestrator
        from app.orchestrators.image_orchestrator import ImageOrchestrator
        from app.orchestrators.product_orchestrator import ProductOrchestrator
        from app.orchestrators.recommendation_orchestrator import RecommendationOrchestrator
        from app.orchestrators.search_orchestrator import SearchOrchestrator
        from app.orchestrators.user_orchestrator import UserOrchestrator
        
        # Search Orchestrator (needed by other orchestrators)
        self._services['search_orchestrator'] = SearchOrchestrator(
            search=self._services['hybrid_search'],
            personalization=self._services['personalization_scorer'],
            cache=self._services['redis']
        )
        
        # Now create SearchTools, VariantTools, PersonalizationTools, and WorkflowTools after search_orchestrator exists
        from app.intelligence.tools.personalization_tools import PersonalizationTools
        from app.intelligence.tools.search_tools import SearchTools
        from app.intelligence.tools.variant_tools import VariantTools
        from app.intelligence.tools.workflow_tools import WorkflowTools
        from app.intelligence.workflow.capability_chain import CapabilityChain
        
        self._services['search_tools'] = SearchTools(
            search_service=self._services['search_orchestrator']
        )
        
        self._services['variant_tools'] = VariantTools(
            hybrid_search=self._services['hybrid_search']
        )
        
        self._services['personalization_tools'] = PersonalizationTools(
            personalization_scorer=self._services['personalization_scorer']
        )
        
        # Create capability chain and workflow tools
        self._services['capability_chain'] = CapabilityChain()
        self._services['workflow_tools'] = WorkflowTools(
            capability_chain=self._services['capability_chain'],
            image_tools=None,  # Will be set after chat orchestrator creation
            variant_tools=self._services['variant_tools'],
            personalization_tools=self._services['personalization_tools'],
            product_tools=self._services['product_tools']
        )
        
        # Chat Orchestrator
        self._services['chat_orchestrator'] = ChatOrchestrator(
            llm_engine=self._services['llm_engine'],
            memory=self._services['short_term_memory'],
            user_service=self._services['user_service'],
            conversation_service=self._services['conversation_service'],
            image_processor=self._services['image_processor'],
            product_tools=self._services['product_tools'],
            user_tools=self._services['user_tools']
        )
        
        # Set variant tools on chat orchestrator
        self._services['chat_orchestrator'].set_variant_tools(self._services['variant_tools'])
        
        # Set personalization tools on chat orchestrator
        self._services['chat_orchestrator'].set_personalization_tools(self._services['personalization_tools'])
        
        # Set workflow tools on chat orchestrator and update workflow tools with image tools
        self._services['chat_orchestrator'].set_workflow_tools(self._services['workflow_tools'])
        if self._services['chat_orchestrator'].image_tools:
            self._services['workflow_tools'].image_tools = self._services['chat_orchestrator'].image_tools
        
        # Conversation Orchestrator
        self._services['conversation_orchestrator'] = ConversationOrchestrator(
            conversation_service=self._services['conversation_service']
        )
        
        # Product Orchestrator
        self._services['product_orchestrator'] = ProductOrchestrator(
            product_service=self._services['product_service'],
            user_service=self._services['user_service'],
            trending_service=self._services['trending_products_service']
        )
        
        # User Orchestrator
        self._services['user_orchestrator'] = UserOrchestrator(
            user_service=self._services['user_service']
        )
        
        # Recommendation Orchestrator
        self._services['recommendation_orchestrator'] = RecommendationOrchestrator(
            recommendation_engine=self._services['recommendation_engine'],
            user_service=self._services['user_service'],
            product_service=self._services['product_service']
        )
        
        # Image Orchestrator
        self._services['image_orchestrator'] = ImageOrchestrator(
            image_processor=self._services['image_processor'],
            search_service=self._services['hybrid_search']
        )
        
        logger.info("Orchestrators initialized")
    
    async def cleanup(self) -> None:
        """Cleanup all services"""
        logger.info("🛑 Shutting down services...")
        
        # Cleanup in reverse order
        for service_name, service in reversed(list(self._services.items())):
            try:
                if hasattr(service, 'close'):
                    await service.close()
                logger.info(f"✅ Cleaned up {service_name}")
            except Exception as e:
                logger.error(f"❌ Failed to cleanup {service_name}: {e}")
        
        self._services.clear()
        self._initialized = False
        logger.info("👋 Shutdown complete")
    
    def get(self, service_name: str) -> Any:
        """Get service by name"""
        return self._services.get(service_name)
    
    def is_initialized(self) -> bool:
        """Check if container is initialized"""
        return self._initialized


@lru_cache()
def get_container() -> Container:
    """Get singleton container instance"""
    return Container()
