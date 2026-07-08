"""
PostgreSQL Database Client
Layer 6: Infrastructure - Data & State
Async PostgreSQL with SQLAlchemy
"""
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.db.models import Activity, Base, Conversation, Message, Product, User
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
                pool_size=20,
                max_overflow=10,
                pool_pre_ping=True
            )
            
            self.async_session = sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
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
    
    async def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product by ID"""
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(Product).where(Product.id == product_id)
                )
                product = result.scalar_one_or_none()
                
                if product:
                    return self._product_to_dict(product)
                return None
                
        except Exception as e:
            logger.error(f"Error getting product {product_id}: {e}")
            return None
    
    async def search_products(
        self, 
        filters: Dict[str, Any], 
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Search products with filters"""
        try:
            async with self.async_session() as session:
                query = select(Product)
                
                # Apply filters
                if filters.get('category'):
                    query = query.where(Product.category == filters['category'])
                if filters.get('sub_category'):
                    query = query.where(Product.sub_category == filters['sub_category'])
                if filters.get('brand'):
                    query = query.where(Product.brand == filters['brand'])
                if filters.get('online_available'):
                    query = query.where(Product.online_available == 1)
                if filters.get('stock'):
                    query = query.where(Product.stock > 0)
                if filters.get('rating_min'):
                    query = query.where(Product.rating >= filters['rating_min'])
                
                # Exclude specific product
                if filters.get('exclude_id'):
                    query = query.where(Product.id != filters['exclude_id'])
                
                # Pagination
                query = query.offset(offset).limit(limit)
                
                result = await session.execute(query)
                products = result.scalars().all()
                
                return [self._product_to_dict(p) for p in products]
                
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
    
    async def upsert_product(self, product_data: Dict[str, Any]) -> bool:
        """Insert or update product"""
        from datetime import datetime

        def _parse_dt(val):
            if val is None or isinstance(val, datetime):
                return val
            try:
                return datetime.fromisoformat(str(val).replace('Z', '+00:00')).replace(tzinfo=None)
            except Exception:
                return None

        try:
            async with self.async_session() as session:
                product = Product(
                    id=product_data['id'],
                    name=product_data.get('name'),
                    title=product_data.get('title'),
                    brand=product_data.get('brand'),
                    category=product_data.get('category'),
                    sub_category=product_data.get('sub_category'),
                    description=product_data.get('description'),
                    url=product_data.get('url'),
                    price=product_data.get('price'),
                    price_history=product_data.get('price_history'),
                    tags=product_data.get('tags'),
                    images=product_data.get('images'),
                    availability=product_data.get('availability'),
                    extra_data=product_data.get('metadata'),
                    rating=product_data.get('rating', 0.0),
                    stock=bool(product_data.get('stock', False)),
                    online_available=bool(product_data.get('online_available', True)),
                    uploaded_at=_parse_dt(product_data.get('uploaded_at')),
                )
                
                await session.merge(product)
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error upserting product: {e}")
            return False
    
    # ==================== User Operations ====================
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if user:
                    return self._user_to_dict(user)
                return None
                
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def upsert_user(self, user_data: Dict[str, Any]) -> bool:
        """Insert or update user"""
        def _parse_dt(val):
            if val is None:
                return None
            if hasattr(val, 'tzinfo') and val.tzinfo is not None:
                return val.replace(tzinfo=None)
            return val

        try:
            async with self.async_session() as session:
                user = User(
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
        user_id: str, 
        preferences: Dict[str, Any]
    ) -> bool:
        """Update user preferences"""
        try:
            async with self.async_session() as session:
                await session.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(preferences=preferences)
                )
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False
    
    # ==================== Conversation Operations ====================
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation"""
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(Conversation).where(Conversation.id == conversation_id)
                )
                conv = result.scalar_one_or_none()
                
                if conv:
                    return self._conversation_to_dict(conv)
                return None
                
        except Exception as e:
            logger.error(f"Error getting conversation: {e}")
            return None
    async def _ensure_user_exists(self, session, user_id: str):
        """Ensure that the user exists in database to satisfy foreign keys"""
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            try:
                async with session.begin_nested():
                    user = User(id=user_id, name=f"User {user_id}")
                    session.add(user)
                    await session.flush()
            except Exception:
                pass

    async def create_conversation(
        self, 
        conversation_id: str, 
        user_id: str, 
        title: str = None
    ) -> bool:
        """Create conversation"""
        try:
            async with self.async_session() as session:
                await self._ensure_user_exists(session, user_id)
                conv = Conversation(
                    id=conversation_id,
                    user_id=user_id,
                    title=title or "New Chat"
                )
                session.add(conv)
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return False
    
    async def save_message(
        self, 
        message_id: str,
        conversation_id: str,
        user_id: str,
        role: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Save message"""
        try:
            async with self.async_session() as session:
                await self._ensure_user_exists(session, user_id)
                # Ensure conversation exists
                res = await session.execute(select(Conversation).where(Conversation.id == conversation_id))
                conv = res.scalar_one_or_none()
                if not conv:
                    conv = Conversation(
                        id=conversation_id,
                        user_id=user_id,
                        title="New Chat"
                    )
                    session.add(conv)
                    await session.flush()
                
                message = Message(
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
        conversation_id: str, 
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get conversation messages"""
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(Message)
                    .where(Message.conversation_id == conversation_id)
                    .order_by(Message.created_at.desc())
                    .offset(offset)
                    .limit(limit)
                )
                messages = result.scalars().all()
                
                return [self._message_to_dict(m) for m in reversed(messages)]
                
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    # ==================== Activity Operations ====================
    
    async def log_user_activity(self, activity_data: Dict[str, Any]) -> bool:
        """Log user activity"""
        try:
            async with self.async_session() as session:
                activity = Activity(
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
    
    def _user_to_dict(self, user: User) -> Dict[str, Any]:
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
    
    def _conversation_to_dict(self, conv: Conversation) -> Dict[str, Any]:
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
    
    def _message_to_dict(self, message: Message) -> Dict[str, Any]:
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

    
    async def get_conversations_by_user(self, user_id: str, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        try:
            async with self.async_session() as session:
                query = select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.created_at.desc()).offset(offset).limit(limit)
                result = await session.execute(query)
                return [self._conversation_to_dict(c) for c in result.scalars().all()]
        except Exception as e:
            logger.error(f"Error querying conversations: {e}")
            return []

    async def update_user(self, user_id: str, data: dict[str, Any]) -> bool:
        try:
            async with self.async_session() as session:
                await self._ensure_user_exists(session, user_id)
                result = await session.execute(select(User).where(User.id == user_id))
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

    async def delete_conversation(self, conversation_id: str) -> bool:
        try:
            async with self.async_session() as session:
                await session.execute(delete(Message).where(Message.conversation_id == conversation_id))
                await session.execute(delete(Conversation).where(Conversation.id == conversation_id))
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting doc {conversation_id}: {e}")
            return False
