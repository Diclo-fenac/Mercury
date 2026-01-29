"""
Service Container
Dependency injection container for managing service instances
"""
import asyncio
from typing import Dict, Any, Optional, Type, TypeVar, Generic, List
from abc import ABC, abstractmethod

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("container")

T = TypeVar('T')

class ServiceInterface(ABC):
    """Base interface for all services"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup service resources"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check service health"""
        pass

class ServiceContainer:
    """
    Service container for dependency injection
    Manages service lifecycle and dependencies
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._service_configs: Dict[str, Dict[str, Any]] = {}
        self._initialized = False
        self.settings = get_settings()
    
    def register_service(
        self, 
        name: str, 
        service_class: Type[T], 
        config: Optional[Dict[str, Any]] = None,
        singleton: bool = True
    ) -> None:
        """Register a service class"""
        self._service_configs[name] = {
            'class': service_class,
            'config': config or {},
            'singleton': singleton,
            'instance': None
        }
        logger.info(f"📝 Registered service: {name}")
    
    async def get_service(self, name: str) -> Optional[Any]:
        """Get service instance"""
        if name not in self._service_configs:
            logger.error(f"❌ Service not registered: {name}")
            return None
        
        config = self._service_configs[name]
        
        # Return existing instance if singleton
        if config['singleton'] and config['instance']:
            return config['instance']
        
        # Create new instance
        try:
            service_class = config['class']
            service_config = config['config']
            
            # Create instance
            if asyncio.iscoroutinefunction(service_class.__init__):
                instance = await service_class(**service_config)
            else:
                instance = service_class(**service_config)
            
            # Initialize if it's a ServiceInterface
            if isinstance(instance, ServiceInterface):
                await instance.initialize()
            
            # Store instance if singleton
            if config['singleton']:
                config['instance'] = instance
            
            logger.info(f"✅ Created service instance: {name}")
            return instance
            
        except Exception as e:
            logger.error(f"💥 Failed to create service {name}: {e}")
            return None
    
    async def initialize_async_services(self) -> None:
        """Initialize all registered services"""
        if self._initialized:
            return
        
        logger.info("🔧 Initializing services...")
        
        # Register all services
        await self._register_all_services()
        
        # Initialize core services first
        core_services = ['redis', 'firestore', 'llm']
        for service_name in core_services:
            if service_name in self._service_configs:
                await self.get_service(service_name)
        
        # Initialize other services
        for service_name in self._service_configs:
            if service_name not in core_services:
                await self.get_service(service_name)
        
        self._initialized = True
        logger.info("✅ All services initialized")
    
    async def cleanup_async_services(self) -> None:
        """Cleanup all service instances"""
        logger.info("🧹 Cleaning up services...")
        
        for name, config in self._service_configs.items():
            instance = config.get('instance')
            if instance and isinstance(instance, ServiceInterface):
                try:
                    await instance.cleanup()
                    logger.info(f"✅ Cleaned up service: {name}")
                except Exception as e:
                    logger.error(f"❌ Failed to cleanup service {name}: {e}")
        
        self._services.clear()
        self._initialized = False
        logger.info("✅ Service cleanup complete")
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all services"""
        health_status = {}
        
        for name, config in self._service_configs.items():
            instance = config.get('instance')
            if instance and isinstance(instance, ServiceInterface):
                try:
                    health_status[name] = await instance.health_check()
                except Exception as e:
                    logger.error(f"Health check failed for {name}: {e}")
                    health_status[name] = False
            else:
                health_status[name] = instance is not None
        
        return health_status
    
    async def _register_all_services(self) -> None:
        """Register all application services"""
        # Import services here to avoid circular imports
        from app.services.redis_service import RedisService
        from app.services.llm_service import LLMService
        from app.services.user_service import UserService
        from app.services.product_service import ProductService
        from app.services.chat_service import ChatService
        from app.services.conversation_service import ConversationService
        from app.services.image_service import ImageService
        from app.services.search_service import SearchService
        from app.services.firestore_service import FirestoreService
        
        # Register Redis service
        self.register_service(
            'redis',
            RedisService,
            {
                'host': self.settings.REDIS_HOST,
                'port': self.settings.REDIS_PORT,
                'db': self.settings.REDIS_DB,
                'password': self.settings.REDIS_PASSWORD,
                'url': self.settings.REDIS_URL
            }
        )
        
        # Register Firestore service
        self.register_service(
            'firestore',
            FirestoreService,
            {
                'project_id': self.settings.GOOGLE_CLOUD_PROJECT,
                'credentials_path': self.settings.GOOGLE_APPLICATION_CREDENTIALS,
                'collection_name': self.settings.FIRESTORE_COLLECTION
            }
        )
        
        # Register LLM service
        self.register_service(
            'llm',
            LLMService,
            {
                'api_key': self.settings.GOOGLE_API_KEY,
                'project_id': self.settings.GOOGLE_CLOUD_PROJECT
            }
        )
        
        # Register User service
        self.register_service('user', UserService)
        
        # Register Product service
        self.register_service('product', ProductService)
        
        # Register Chat service
        self.register_service('chat', ChatService)
        
        # Register Conversation service
        self.register_service('conversation', ConversationService)
        
        # Register Image service
        self.register_service(
            'image_processing',
            ImageService,
            {
                'bucket_name': self.settings.GCS_BUCKET_NAME,
                'max_file_size': self.settings.MAX_FILE_SIZE,
                'allowed_types': self.settings.ALLOWED_FILE_TYPES
            }
        )
        
        # Register Search service
        self.register_service(
            'search',
            SearchService,
            {
                'qdrant_host': self.settings.QDRANT_HOST,
                'qdrant_port': self.settings.QDRANT_PORT,
                'qdrant_api_key': self.settings.QDRANT_API_KEY,
                'collection_name': self.settings.QDRANT_COLLECTION_NAME
            }
        )
    
    def is_initialized(self) -> bool:
        """Check if container is initialized"""
        return self._initialized
    
    def get_registered_services(self) -> List[str]:
        """Get list of registered service names"""
        return list(self._service_configs.keys())
    
    async def restart_service(self, name: str) -> bool:
        """Restart a specific service"""
        if name not in self._service_configs:
            return False
        
        try:
            # Cleanup existing instance
            config = self._service_configs[name]
            instance = config.get('instance')
            if instance and isinstance(instance, ServiceInterface):
                await instance.cleanup()
            
            # Clear instance
            config['instance'] = None
            
            # Create new instance
            new_instance = await self.get_service(name)
            return new_instance is not None
            
        except Exception as e:
            logger.error(f"Failed to restart service {name}: {e}")
            return False