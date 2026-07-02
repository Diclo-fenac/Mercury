"""
SQLAlchemy Models
PostgreSQL tables with JSONB columns
"""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Product(Base):
    """Product table with JSONB for flexible schema"""
    __tablename__ = 'products'

    id = Column(String(255), primary_key=True)
    name = Column(String(500), nullable=False)
    title = Column(String(500))
    brand = Column(String(255))
    category = Column(String(255))
    sub_category = Column(String(255))
    description = Column(Text)
    url = Column(Text)

    # JSONB columns for flexible data
    price = Column(JSONB)           # {actual, selling, discount_percent}
    price_history = Column(JSONB)   # [{date, price}, ...]
    tags = Column(JSONB)            # {Fabric, Size, Color, ...}
    images = Column(JSONB)          # [url, ...]
    availability = Column(JSONB)    # [{store_id, aisle, shelf, quantity, is_backstock}, ...]
    extra_data = Column('metadata', JSONB)

    # Search fields
    rating = Column(Float, default=0.0)
    stock = Column(Boolean, default=False)
    online_available = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    uploaded_at = Column(DateTime)

    __table_args__ = (
        Index('idx_products_brand', 'brand'),
        Index('idx_products_category', 'category'),
        Index('idx_products_sub_category', 'sub_category'),
        Index('idx_products_rating', 'rating'),
        Index('idx_products_tags', 'tags', postgresql_using='gin'),
        Index('idx_products_price', 'price', postgresql_using='gin'),
        Index('idx_products_availability', 'availability', postgresql_using='gin'),
    )


class Store(Base):
    """Physical store table"""
    __tablename__ = 'stores'

    id = Column(String(255), primary_key=True)  # e.g. WM_STORE_001
    name = Column(String(500))
    location = Column(JSONB)        # {address, city, state, zip, lat, lon}
    hours = Column(JSONB)           # {open, close}
    aisle_mapping = Column(JSONB)   # {category: [aisle_codes]}
    connected_stores = Column(JSONB)  # [store_id, ...]

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_stores_location', 'location', postgresql_using='gin'),
    )


class User(Base):
    """User table with JSONB for preferences and behavior"""
    __tablename__ = 'users'
    
    id = Column(String(255), primary_key=True)
    email = Column(String(255), unique=True)
    name = Column(String(255))
    gender = Column(String(50))
    
    # JSONB columns
    preferences = Column(JSONB)  # {budget_range, preferred_brands, preferred_categories, preferred_colors, preferred_size}
    behavior = Column(JSONB)    # {most_viewed_products, stats, last_activity}
    health = Column(JSONB)      # array of health conditions
    location = Column(JSONB)    # {address, city, state, lat, lon}
    extra_data = Column('metadata', JSONB)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_preferences', 'preferences', postgresql_using='gin'),
        Index('idx_users_behavior', 'behavior', postgresql_using='gin'),
    )


class Conversation(Base):
    """Conversation table"""
    __tablename__ = 'conversations'
    
    id = Column(String(255), primary_key=True)
    user_id = Column(String(255), ForeignKey('users.id'), nullable=False)
    title = Column(String(500))
    
    # JSONB for metadata
    extra_data = Column('metadata', JSONB)
    
    # Stats
    message_count = Column(Integer, default=0)
    last_message_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_conversations_user_id', 'user_id'),
        Index('idx_conversations_last_message', 'last_message_at'),
    )


class Message(Base):
    """Message table for conversation history"""
    __tablename__ = 'messages'
    
    id = Column(String(255), primary_key=True)
    conversation_id = Column(String(255), ForeignKey('conversations.id'), nullable=False)
    user_id = Column(String(255), ForeignKey('users.id'), nullable=False)
    
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # JSONB for metadata
    extra_data = Column('metadata', JSONB)  # {type: str, image_analysis: {}, function_called: str}
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        Index('idx_messages_conversation_id', 'conversation_id'),
        Index('idx_messages_user_id', 'user_id'),
        Index('idx_messages_created_at', 'created_at'),
    )


class Barcode(Base):
    """Barcode table linked to products via pid"""
    __tablename__ = 'barcodes'

    id = Column(String(255), primary_key=True)  # barcode value (document ID)
    barcode = Column(String(255), nullable=False)
    barcode_type = Column(String(50))  # e.g. UPC-A, EAN-13
    pid = Column(String(255))  # product ID reference
    status = Column(String(50), default='active')
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_barcodes_pid', 'pid'),
        Index('idx_barcodes_barcode', 'barcode'),
        Index('idx_barcodes_status', 'status'),
    )


class Activity(Base):
    """User activity log"""
    __tablename__ = 'activities'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey('users.id'), nullable=False)
    
    activity_type = Column(String(100), nullable=False)  # search, view, purchase, etc.
    
    # JSONB for activity data
    data = Column(JSONB)  # {product_id: str, query: str, ...}
    
    # Timestamp
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        Index('idx_activities_user_id', 'user_id'),
        Index('idx_activities_type', 'activity_type'),
        Index('idx_activities_created_at', 'created_at'),
    )
