"""
PostgreSQL Database Client
Layer 6: Infrastructure - Data & State
Async PostgreSQL with SQLAlchemy
"""
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.domain.tenants.models import CatalogItem
from app.infrastructure.db.models import (
    Product,
    TenantActivity,
    TenantConversation,
    TenantMessage,
    TenantUser,
)
from app.utils.logger import get_logger

logger = get_logger("postgres")


class PostgresClient:
    """Async PostgreSQL client with SQLAlchemy"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.async_session = None
        self._connected = False
    
    async def connect(self) -> None:
        """Initialize PostgreSQL connection"""
        try:
            self.engine = create_async_engine(
                self.database_url,
                echo=False,
                pool_size=10,
                max_overflow=5,
                pool_pre_ping=True
            )
            
            self.async_session = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Schema is owned by Alembic. Runtime DDL masks migration drift and can
            # create partially upgraded databases, so only verify connectivity here.
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            
            self._connected = True
            logger.info("✅ PostgreSQL connected")
            
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            raise
    
    def setup_sync(self, embeddings, typesense) -> None:
        """Wire up the sync pipeline and register ORM event triggers."""
        from app.infrastructure.sync.pipeline import SyncPipeline
        from app.infrastructure.sync.triggers import register_triggers

        pipeline = SyncPipeline(
            embeddings=embeddings,
            typesense=typesense,
            collection_name="products",
        )
        register_triggers(pipeline)
        logger.info("✅ Sync pipeline wired to PostgresClient")

    async def close(self) -> None:
        """Close PostgreSQL connection"""
        if self.engine:
            await self.engine.dispose()
        self._connected = False
        logger.info("✅ PostgreSQL connection closed")
    
    async def health_check(self) -> bool:
        """Check PostgreSQL health"""
        if not self._connected:
            return False
        
        try:
            async with self.async_session() as session:
                await session.execute(select(1))
            return True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False
    
    # ==================== Product Operations ====================
    
    def _product_scope(self, organization_id: str, product_id: Optional[str]) -> tuple[str, str]:
        """Resolve legacy reads only from request tenant context; never query global products."""
        if product_id is not None:
            return organization_id, product_id
        from app.core.security.context import tenant_context_var

        tenant = tenant_context_var.get()
        if not tenant:
            raise ValueError("Tenant context required for catalog reads")
        return tenant.organization_id, organization_id

    async def get_product_by_id(
        self, organization_id: str, product_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get one canonical product only within its organization."""
        try:
            organization_id, product_id = self._product_scope(organization_id, product_id)
            org_id = self._organization_uuid(organization_id)
            async with self.async_session() as session:
                product = await session.scalar(
                    select(CatalogItem).where(
                        CatalogItem.organization_id == org_id,
                        CatalogItem.external_id == product_id,
                        CatalogItem.resource_type == "product",
                        CatalogItem.status == "active",
                        CatalogItem.deleted_at.is_(None),
                    )
                )
                if product:
                    return self._catalog_item_to_dict(product)
                return None
                
        except Exception as e:
            logger.error(f"Error getting product {product_id}: {e}")
            return None

    async def get_products_by_ids(
        self, organization_id: str, product_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Rehydrate derived-search IDs from canonical catalog in one tenant-scoped query."""
        if not product_ids:
            return {}
        try:
            org_id = self._organization_uuid(organization_id)
            async with self.async_session() as session:
                result = await session.scalars(
                    select(CatalogItem).where(
                        CatalogItem.organization_id == org_id,
                        CatalogItem.external_id.in_([str(product_id) for product_id in product_ids]),
                        CatalogItem.resource_type == "product",
                        CatalogItem.status == "active",
                        CatalogItem.deleted_at.is_(None),
                    )
                )
                return {
                    item.external_id: self._catalog_item_to_dict(item)
                    for item in result.all()
                }
        except Exception as exc:
            logger.error(f"Error rehydrating canonical products: {exc}")
            return {}
    
    async def search_products(
        self,
        organization_id: str | Dict[str, Any],
        filters: Optional[Dict[str, Any] | int] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Search canonical products in one organization, never global legacy rows."""
        try:
            if isinstance(organization_id, dict):
                # Legacy shape: search_products(filters, limit). It is safe only under
                # a request-scoped tenant context set by the orchestrator.
                if isinstance(filters, int):
                    limit = filters
                filters = organization_id
                from app.core.security.context import tenant_context_var

                tenant = tenant_context_var.get()
                if not tenant:
                    raise ValueError("Tenant context required for catalog reads")
                organization_id = tenant.organization_id
            filters = filters if isinstance(filters, dict) else {}
            org_id = self._organization_uuid(str(organization_id))
            async with self.async_session() as session:
                query = select(CatalogItem).where(
                    CatalogItem.organization_id == org_id,
                    CatalogItem.resource_type == "product",
                    CatalogItem.status == "active",
                    CatalogItem.deleted_at.is_(None),
                )

                # Apply filters
                if filters.get('category'):
                    query = query.where(CatalogItem.category == filters['category'])
                if filters.get('sub_category'):
                    query = query.where(CatalogItem.sub_category == filters['sub_category'])
                if filters.get('brand'):
                    query = query.where(CatalogItem.brand == filters['brand'])
                if filters.get('online_available'):
                    query = query.where(CatalogItem.document['online_available'].as_boolean().is_(True))
                if filters.get('stock'):
                    query = query.where(CatalogItem.document['stock'].as_boolean().is_(True))
                
                # Exclude specific product
                if filters.get('exclude_id'):
                    query = query.where(CatalogItem.external_id != str(filters['exclude_id']))
                if filters.get('seller_id'):
                    query = query.where(CatalogItem.seller_id == str(filters['seller_id']))
                
                # Pagination
                query = query.offset(offset).limit(limit)
                
                result = await session.execute(query)
                return [self._catalog_item_to_dict(product) for product in result.scalars().all()]
                
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
    
    async def upsert_product(self, product_data: Dict[str, Any]) -> bool:
        """Legacy global writes are intentionally disabled; use CatalogService."""
        raise RuntimeError("Use CatalogService.upsert_products for tenant-scoped catalog writes")
    
    # ==================== User Operations ====================
    
    @staticmethod
    def _organization_uuid(organization_id: str) -> UUID:
        return UUID(str(organization_id))

    async def get_user_profile(self, organization_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        try:
            org_id = self._organization_uuid(organization_id)
            async with self.async_session() as session:
                result = await session.execute(
                    select(TenantUser).where(
                        TenantUser.organization_id == org_id,
                        TenantUser.id == user_id,
                    )
                )
                user = result.scalar_one_or_none()
                
                if user:
                    return self._user_to_dict(user)
                return None
                
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def upsert_user(self, organization_id: str, user_data: Dict[str, Any]) -> bool:
        """Insert or update user"""
        def _parse_dt(val):
            if val is None:
                return None
            if hasattr(val, 'tzinfo') and val.tzinfo is not None:
                return val.replace(tzinfo=None)
            return val

        try:
            org_id = self._organization_uuid(organization_id)
            async with self.async_session() as session:
                user = TenantUser(
                    organization_id=org_id,
                    id=user_data['id'],
                    email=user_data.get('email'),
                    name=user_data.get('name'),
                    gender=user_data.get('gender'),
                    preferences=user_data.get('preferences'),
                    behavior=user_data.get('behavior'),
                    health=user_data.get('health'),
                    location=user_data.get('location'),
                    extra_data=user_data.get('metadata')
                )
                
                await session.merge(user)
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error upserting user: {e}")
            return False
    
    async def update_user_preferences(
        self,
        organization_id: str,
        user_id: str,
        preferences: Dict[str, Any],
    ) -> bool:
        """Update user preferences"""
        try:
            org_id = self._organization_uuid(organization_id)
            async with self.async_session() as session:
                await session.execute(
                    update(TenantUser)
                    .where(TenantUser.organization_id == org_id, TenantUser.id == user_id)
                    .values(preferences=preferences)
                )
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False
    
    # ==================== Conversation Operations ====================
    
    async def get_conversation(self, organization_id: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation"""
        try:
            org_id = self._organization_uuid(organization_id)
            async with self.async_session() as session:
                result = await session.execute(
                    select(TenantConversation).where(
                        TenantConversation.organization_id == org_id,
                        TenantConversation.id == conversation_id,
                    )
                )
                conv = result.scalar_one_or_none()
                
                if conv:
                    return self._conversation_to_dict(conv)
                return None
                
        except Exception as e:
            logger.error(f"Error getting conversation: {e}")
            return None
    async def _ensure_tenant_user_exists(self, session, organization_id: UUID, user_id: str):
        """Ensure that the user exists in database to satisfy foreign keys"""
        result = await session.execute(
            select(TenantUser).where(
                TenantUser.organization_id == organization_id,
                TenantUser.id == user_id,
            )
        )
        user = result.scalar_one_or_none()
        if not user:
            try:
                async with session.begin_nested():
                    user = TenantUser(
                        organization_id=organization_id,
                        id=user_id,
                        name=f"User {user_id}",
                    )
                    session.add(user)
                    await session.flush()
            except Exception:
                pass

    async def create_conversation(
        self,
        organization_id: str,
        conversation_id: str,
        user_id: str,
        title: str = None,
        channel: str = "rest",
    ) -> bool:
        """Create conversation"""
        try:
            org_id = self._organization_uuid(organization_id)
            async with self.async_session() as session:
                await self._ensure_tenant_user_exists(session, org_id, user_id)
                conv = TenantConversation(
                    organization_id=org_id,
                    id=conversation_id,
                    user_id=user_id,
                    title=title or "New Chat",
                    channel=channel,
                )
                session.add(conv)
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return False
    
    async def save_message(
        self,
        organization_id: str,
        message_id: str,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """Save message"""
        try:
            org_id = self._organization_uuid(organization_id)
            async with self.async_session() as session:
                await self._ensure_tenant_user_exists(session, org_id, user_id)
                # Ensure conversation exists
                res = await session.execute(
                    select(TenantConversation).where(
                        TenantConversation.organization_id == org_id,
                        TenantConversation.id == conversation_id,
                    )
                )
                conv = res.scalar_one_or_none()
                if not conv:
                    conv = TenantConversation(
                        organization_id=org_id,
                        id=conversation_id,
                        user_id=user_id,
                        title="New Chat",
                    )
                    session.add(conv)
                    await session.flush()
                
                message = TenantMessage(
                    organization_id=org_id,
                    id=message_id,
                    conversation_id=conversation_id,
                    user_id=user_id,
                    role=role,
                    content=content,
                    extra_data=metadata
                )
                session.add(message)
                
                # Update conversation stats
                conv.message_count = (conv.message_count or 0) + 1
                conv.last_message_at = func.now()
                
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return False
    
    async def get_messages(
        self,
        organization_id: str,
        conversation_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get conversation messages"""
        try:
            org_id = self._organization_uuid(organization_id)
            async with self.async_session() as session:
                result = await session.execute(
                    select(TenantMessage)
                    .where(
                        TenantMessage.organization_id == org_id,
                        TenantMessage.conversation_id == conversation_id,
                    )
                    .order_by(TenantMessage.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
                messages = result.scalars().all()
                
                return [self._message_to_dict(m) for m in reversed(messages)]
                
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    # ==================== Activity Operations ====================
    
    async def log_user_activity(self, organization_id: str, activity_data: Dict[str, Any]) -> bool:
        """Log user activity"""
        try:
            org_id = self._organization_uuid(organization_id)
            async with self.async_session() as session:
                await self._ensure_tenant_user_exists(session, org_id, activity_data['user_id'])
                activity = TenantActivity(
                    organization_id=org_id,
                    user_id=activity_data['user_id'],
                    activity_type=activity_data['activity_type'],
                    data=activity_data.get('data')
                )
                session.add(activity)
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
            return False
    
    # ==================== Helper Methods ====================
    
    def _product_to_dict(self, product: Product) -> Dict[str, Any]:
        """Convert Product model to dict"""
        return {
            'id': product.id,
            'name': product.name,
            'title': product.title,
            'brand': product.brand,
            'category': product.category,
            'sub_category': product.sub_category,
            'description': product.description,
            'url': product.url,
            'price': product.price,
            'price_history': product.price_history,
            'tags': product.tags,
            'images': product.images,
            'availability': product.availability,
            'metadata': product.extra_data,
            'rating': product.rating,
            'stock': bool(product.stock),
            'online_available': bool(product.online_available),
            'created_at': product.created_at,
            'updated_at': product.updated_at,
            'uploaded_at': product.uploaded_at,
        }

    @staticmethod
    def _catalog_item_to_dict(item: CatalogItem) -> Dict[str, Any]:
        """Expose canonical document while preserving normalized searchable fields."""
        document = dict(item.document or {})
        return {
            **document,
            'id': document.get('id', item.external_id),
            'name': document.get('name', item.title),
            'title': document.get('title', item.title),
            'brand': document.get('brand', item.brand),
            'category': document.get('category', item.category),
            'sub_category': document.get('sub_category', item.sub_category),
            'description': document.get('description', item.description),
            'url': document.get('url', item.url),
        }
    
    def _user_to_dict(self, user: TenantUser) -> Dict[str, Any]:
        """Convert User model to dict"""
        return {
            'id': user.id,
            'email': user.email,
            'name': user.name,
            'gender': user.gender,
            'preferences': user.preferences,
            'behavior': user.behavior,
            'health': user.health,
            'location': user.location,
            'metadata': user.extra_data,
            'created_at': user.created_at,
            'updated_at': user.updated_at
        }
    
    def _conversation_to_dict(self, conv: TenantConversation) -> Dict[str, Any]:
        """Convert Conversation model to dict"""
        return {
            'id': conv.id,
            'conversation_id': conv.id,
            'user_id': conv.user_id,
            'title': conv.title,
            'metadata': conv.extra_data,
            'message_count': conv.message_count,
            'last_message_at': conv.last_message_at,
            'created_at': conv.created_at,
            'updated_at': conv.updated_at
        }
    
    def _message_to_dict(self, message: TenantMessage) -> Dict[str, Any]:
        """Convert Message model to dict"""
        return {
            'id': message.id,
            'conversation_id': message.conversation_id,
            'user_id': message.user_id,
            'role': message.role,
            'content': message.content,
            'metadata': message.extra_data,
            'created_at': message.created_at
        }

    
    async def get_conversations_by_user(
        self,
        organization_id: str,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        try:
            org_id = self._organization_uuid(organization_id)
            async with self.async_session() as session:
                query = (
                    select(TenantConversation)
                    .where(
                        TenantConversation.organization_id == org_id,
                        TenantConversation.user_id == user_id,
                    )
                    .order_by(TenantConversation.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
                result = await session.execute(query)
                return [self._conversation_to_dict(c) for c in result.scalars().all()]
        except Exception as e:
            logger.error(f"Error querying conversations: {e}")
            return []

    async def update_user(self, organization_id: str, user_id: str, data: dict[str, Any]) -> bool:
        try:
            org_id = self._organization_uuid(organization_id)
            async with self.async_session() as session:
                await self._ensure_tenant_user_exists(session, org_id, user_id)
                result = await session.execute(
                    select(TenantUser).where(
                        TenantUser.organization_id == org_id,
                        TenantUser.id == user_id,
                    )
                )
                user = result.scalar_one_or_none()
                if not user: return False
                for key, val in data.items():
                    if hasattr(user, key):
                        setattr(user, key, val)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return False

    async def delete_conversation(self, organization_id: str, conversation_id: str) -> bool:
        try:
            org_id = self._organization_uuid(organization_id)
            async with self.async_session() as session:
                await session.execute(
                    delete(TenantMessage).where(
                        TenantMessage.organization_id == org_id,
                        TenantMessage.conversation_id == conversation_id,
                    )
                )
                await session.execute(
                    delete(TenantConversation).where(
                        TenantConversation.organization_id == org_id,
                        TenantConversation.id == conversation_id,
                    )
                )
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting doc {conversation_id}: {e}")
            return False
