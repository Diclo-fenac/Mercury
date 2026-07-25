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
        from app.infrastructure.db.postgres import PostgresClient
        from app.infrastructure.storage.local import LocalStorageClient
        
        # Redis - try to connect, continue if fails
        try:
            self._services['redis'] = RedisClient(
                host=self.settings.REDIS_HOST,
                port=self.settings.REDIS_PORT,
                db=self.settings.REDIS_DB,
                password=self.settings.REDIS_PASSWORD,
                url=self.settings.REDIS_URL,
                max_connections=200
            )
            await asyncio.wait_for(self._services['redis'].connect(), timeout=5.0)
            logger.info("Redis connected")
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Redis not available: {e}")
            self._services['redis'] = None
        
        # PostgreSQL - primary database
        try:
            self._services['postgres'] = PostgresClient(
                database_url=self.settings.DATABASE_URL
            )
            await asyncio.wait_for(self._services['postgres'].connect(), timeout=10.0)
            logger.info("PostgreSQL connected")
        except (asyncio.TimeoutError, Exception) as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            raise Exception(f"PostgreSQL is required but failed to connect: {e}")
        
        
        # Typesense - with timeout
        try:
            from app.infrastructure.search.typesense import TypesenseClient
            self._services['typesense'] = TypesenseClient(
                host=self.settings.TYPESENSE_HOST,
                port=self.settings.TYPESENSE_PORT,
                api_key=self.settings.TYPESENSE_API_KEY,
            )
            await asyncio.wait_for(self._services['typesense'].connect(), timeout=5.0)
            logger.info("Typesense connected")
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Typesense not available: {e}")
            self._services['typesense'] = None
        
        # Local or MinIO Storage
        storage_connected = False
        if self.settings.MINIO_ENDPOINT:
            try:
                from app.infrastructure.storage.minio import MinIOStorageClient
                logger.info(f"Connecting to MinIO storage at {self.settings.MINIO_ENDPOINT}...")
                self._services['storage'] = MinIOStorageClient(
                    endpoint=self.settings.MINIO_ENDPOINT,
                    access_key=self.settings.MINIO_ACCESS_KEY,
                    secret_key=self.settings.MINIO_SECRET_KEY,
                    bucket_name=self.settings.MINIO_BUCKET_NAME,
                    secure=self.settings.MINIO_SECURE
                )
                await asyncio.wait_for(self._services['storage'].connect(), timeout=5.0)
                storage_connected = True
                logger.info("MinIO Storage connected successfully")
            except Exception as e:
                logger.warning(f"⚠️ MinIO storage connection failed: {e}. Falling back to Local Storage...")

        if not storage_connected:
            try:
                self._services['storage'] = LocalStorageClient(
                    base_dir="uploads"
                )
                await self._services['storage'].connect()
                logger.info("Local Disk Storage connected (Fallback Mode)")
            except Exception as e:
                logger.error(f"❌ Local Storage connection failed: {e}")
                self._services['storage'] = None

        # GCS alias removed

        
        logger.info("Infrastructure layer initialized")
    
    async def _init_domain_services(self) -> None:
        """Initialize domain services"""
        from app.domain.catalogs.service import CatalogService
        from app.domain.conversations.service import ConversationService
        from app.domain.pricing.service import PricingService
        from app.domain.products.service import ProductService
        from app.domain.products.trending_service import TrendingProductsService
        from app.domain.recommendations.engine import RecommendationEngine
        from app.domain.tenants.audit import AuditService
        from app.domain.users.service import UserService
        from app.infrastructure.catalog.repository import CatalogRepository
        
        # Audit Service
        self._services['audit_service'] = AuditService(
            async_session_maker=self._services['postgres'].async_session
        )
        
        # Product Service
        self._services['product_service'] = ProductService(
            db=self._services['postgres'],
            cache=self._services['redis']
        )
        
        # User Service
        self._services['user_service'] = UserService(
            db=self._services['postgres'],
            cache=self._services['redis']
        )
        
        # Pricing Service
        self._services['pricing_service'] = PricingService()
        
        # Trending Products Service
        self._services['trending_products_service'] = TrendingProductsService(
            cache=self._services['redis'],
            db=self._services['postgres']
        )
        
        # Recommendation Engine
        self._services['recommendation_engine'] = RecommendationEngine(
            product_service=self._services['product_service'],
            user_service=self._services['user_service']
        )
        
        # Conversation Service
        self._services['conversation_service'] = ConversationService(
            db=self._services['postgres'],
            cache=self._services['redis']
        )
        
        # Suggestions Service
        from app.domain.search.suggestions_service import SearchSuggestionsService
        self._services['suggestions_service'] = SearchSuggestionsService(
            cache=self._services['redis'],
            typesense=self._services.get('typesense')
        )

        # Tenant Service & Provisioner
        from app.domain.tenants.provisioning import TenantProvisioner
        from app.domain.tenants.service import TenantService
        self._services['tenant_service'] = TenantService(
            db=self._services['postgres'],
            cache=self._services['redis']
        )
        
        from app.domain.privacy.service import PrivacyService
        self._services['privacy_service'] = PrivacyService(
            db=self._services['postgres'],
            tenant_service=self._services['tenant_service'],
            user_service=self._services['user_service']
        )

        self._services['catalog_service'] = CatalogService(
            repository=CatalogRepository(
                self._services['postgres'],
                max_index_attempts=self.settings.CATALOG_INDEX_MAX_ATTEMPTS,
                processing_lease_seconds=self.settings.CATALOG_INDEX_LEASE_SECONDS,
            )
        )
        self._services['tenant_provisioner'] = TenantProvisioner(
            typesense=self._services.get('typesense')
        )
        
        logger.info("Domain services initialized")
    
    async def _init_addons(self) -> None:
        """Initialize add-ons layer"""
        from app.addons.embeddings.providers.factory import EmbeddingProviderFactory
        from app.addons.image.processor import ImageProcessor
        from app.addons.memory.short_term import ShortTermMemory
        from app.addons.personalization.scorer import PersonalizationScorer
        from app.addons.search.hybrid import HybridSearch

        # 1. Embeddings
        # Default to local sentence-transformers
        if 'embeddings' not in self._services:
            self._services['embeddings'] = EmbeddingProviderFactory.create_provider(self.settings)
            
            # LocalEmbedder has no async initialize, but we'll try if it has one
            if hasattr(self._services['embeddings'], 'initialize'):
                await self._services['embeddings'].initialize()

        # Search
        self._services['hybrid_search'] = HybridSearch(
            typesense=self._services.get('typesense'),
            db=self._services['postgres'],
            embeddings=self._services['embeddings'],
        )
        
        # Memory
        self._services['short_term_memory'] = ShortTermMemory(
            cache=self._services['redis']
        )
        
        # Personalization
        self._services['personalization_scorer'] = PersonalizationScorer(
            user_service=self._services['user_service'],
            privacy_service=self._services['privacy_service'],
            cache=self._services['redis']
        )
        
        # Vision Provider
        provider_type = getattr(self.settings, 'VISION_PROVIDER', 'gemini')
        if provider_type == "openai":
            from app.addons.image.providers.openai import OpenAIVisionProvider
            provider = OpenAIVisionProvider(
                api_key=getattr(self.settings, 'VISION_API_KEY', None),
                api_base=getattr(self.settings, 'VISION_API_BASE', None),
                model_name=getattr(self.settings, 'VISION_MODEL_NAME', 'gpt-4o-mini')
            )
        elif provider_type == "local":
            from app.addons.image.providers.local import LocalVisionProvider
            provider = LocalVisionProvider()
        else:
            from app.addons.image.providers.gemini import GeminiVisionProvider
            # Use specific VISION_API_KEY if present, fallback to GOOGLE_API_KEY
            api_key = getattr(self.settings, 'VISION_API_KEY', None) or getattr(self.settings, 'GOOGLE_API_KEY', None)
            provider = GeminiVisionProvider(
                api_key=api_key,
                model_name=getattr(self.settings, 'VISION_MODEL_NAME', 'gemini-2.5-flash')
            )
            
        await provider.initialize()
        self._services['vision_provider'] = provider
        
        # Image Processor
        self._services['image_processor'] = ImageProcessor(
            storage=self._services['storage'],
            cache=self._services['redis'],
            provider=self._services['vision_provider']
        )

        # Catalog Importer
        from app.domain.tenants.importer import CatalogImporter
        self._services['catalog_importer'] = CatalogImporter(
            typesense=self._services.get('typesense'),
            embeddings=self._services['embeddings'],
            catalog_service=self._services['catalog_service'],
        )
        from app.infrastructure.catalog.worker import CatalogIndexWorker
        self._services['catalog_index_worker'] = CatalogIndexWorker(
            catalog_service=self._services['catalog_service'],
            embeddings=self._services['embeddings'],
            typesense=self._services.get('typesense'),
            tenant_provisioner=self._services.get('tenant_provisioner'),
        )
        
        logger.info("Add-ons layer initialized")
    
    async def _init_intelligence(self) -> None:
        """Initialize intelligence layer"""
        from app.intelligence.engine import LLMEngine
        from app.intelligence.providers.factory import AIProviderFactory
        from app.intelligence.tools.product_tools import ProductTools
        from app.intelligence.tools.user_tools import UserTools
        
        if 'llm_engine' not in self._services:
            self._services['llm_engine'] = AIProviderFactory.create_provider(self.settings)
            await self._services['llm_engine'].initialize()
        else:
            logger.warning("LLM Engine already initialized")
        
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
            cache=self._services['redis'],
            suggestions_service=self._services.get('suggestions_service'),
            tenant_service=self._services.get('tenant_service')
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
    
    async def get_service(self, service_name: str) -> Any:
        """Get service by name (async alias for legacy dependency compatibility)"""
        if not self._initialized:
            await self.initialize()
        return self.get(service_name)
    
    def is_initialized(self) -> bool:
        """Check if container is initialized"""
        return self._initialized


@lru_cache()
def get_container() -> Container:
    """Get singleton container instance"""
    return Container()
