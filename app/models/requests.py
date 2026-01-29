"""
Request Models
Pydantic models for API request validation
"""
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime

# Base models
class BaseRequest(BaseModel):
    """Base request model"""
    user_id: Optional[str] = Field(None, description="User identifier")

# Chat models
class ChatMessage(BaseRequest):
    """Chat message request"""
    message: str = Field(..., min_length=1, max_length=5000, description="Chat message content")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")
    message_type: str = Field(default="text", description="Message type: text, image")
    image_data: Optional[str] = Field(None, description="Base64 encoded image data")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('message_type')
    def validate_message_type(cls, v):
        allowed_types = ['text', 'image']
        if v not in allowed_types:
            raise ValueError(f'message_type must be one of {allowed_types}')
        return v
    
    @validator('image_data')
    def validate_image_data(cls, v, values):
        if values.get('message_type') == 'image' and not v:
            raise ValueError('image_data is required when message_type is image')
        return v

# Search models
class SearchRequest(BaseRequest):
    """Product search request"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    rerank: bool = Field(default=True, description="Enable result reranking")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Search filters")

class AdvancedSearchRequest(BaseRequest):
    """Advanced search with filters"""
    query: Optional[str] = Field(None, description="Search query")
    category: Optional[str] = Field(None, description="Product category")
    sub_category: Optional[str] = Field(None, description="Product sub-category")
    brand: Optional[str] = Field(None, description="Product brand")
    price_range: Optional[Dict[str, float]] = Field(None, description="Price range filter")
    rating_min: Optional[float] = Field(None, ge=0, le=5, description="Minimum rating")
    discount_min: Optional[float] = Field(None, ge=0, le=100, description="Minimum discount percentage")
    stock_only: bool = Field(default=False, description="Only in-stock products")
    online_available: Optional[bool] = Field(None, description="Online availability filter")
    store_id: Optional[str] = Field(None, description="Store identifier")
    sort_by: str = Field(default="relevance", description="Sort criteria")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of results")
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_sorts = ['relevance', 'price_low', 'price_high', 'rating', 'discount']
        if v not in allowed_sorts:
            raise ValueError(f'sort_by must be one of {allowed_sorts}')
        return v

# Image models
class ImageUploadRequest(BaseRequest):
    """Image upload request"""
    image_data: str = Field(..., description="Base64 encoded image data")
    message: str = Field(default="I uploaded an image", description="Associated message")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")
    create_chat_message: bool = Field(default=False, description="Create chat message")
    
    @validator('image_data')
    def validate_image_data(cls, v):
        if not v or not v.startswith('data:image/'):
            raise ValueError('Invalid image data format')
        return v

class ImageSearchRequest(BaseRequest):
    """Image-based search request"""
    image_id: Optional[str] = Field(None, description="Previously uploaded image ID")
    image_data: Optional[str] = Field(None, description="Base64 encoded image data")
    prompt: str = Field(..., min_length=1, description="Search prompt")
    search_type: str = Field(default="exact_and_similar", description="Search type")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    
    @validator('search_type')
    def validate_search_type(cls, v):
        allowed_types = ['exact_match', 'similar_style', 'exact_and_similar']
        if v not in allowed_types:
            raise ValueError(f'search_type must be one of {allowed_types}')
        return v
    
    @validator('image_data')
    def validate_image_requirement(cls, v, values):
        if not v and not values.get('image_id'):
            raise ValueError('Either image_data or image_id is required')
        return v

# User models
class UserPreferencesUpdate(BaseModel):
    """User preferences update"""
    preferences: Dict[str, Any] = Field(..., description="User preferences")
    
class UserActivityLog(BaseRequest):
    """User activity logging"""
    activity_type: str = Field(..., description="Activity type")
    product_id: Optional[str] = Field(None, description="Product identifier")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Activity metadata")

# Session models
class SessionStart(BaseRequest):
    """Session start request"""
    location_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Location information")

# Conversation models
class ConversationCreate(BaseRequest):
    """Create new conversation"""
    title: Optional[str] = Field(None, description="Conversation title")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Conversation metadata")

class ConversationArchive(BaseRequest):
    """Archive conversation request"""
    conversation_id: str = Field(..., description="Conversation identifier")

# WebSocket models
class WebSocketMessage(BaseModel):
    """WebSocket message structure"""
    event: str = Field(..., description="Event type")
    data: Dict[str, Any] = Field(..., description="Event data")
    user_id: Optional[str] = Field(None, description="User identifier")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now, description="Message timestamp")

class WebSocketAuth(BaseModel):
    """WebSocket authentication"""
    user_id: str = Field(..., description="User identifier")
    user_name: Optional[str] = Field(None, description="User display name")
    language: str = Field(default="en", description="User language preference")

class TypingIndicator(BaseModel):
    """Typing indicator message"""
    user_id: str = Field(..., description="User identifier")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")
    typing: bool = Field(..., description="Typing status")

# File upload models
class FileUpload(BaseRequest):
    """File upload via WebSocket"""
    file_data: str = Field(..., description="Base64 encoded file data")
    file_name: str = Field(..., description="Original file name")
    file_type: str = Field(..., description="MIME type")
    conversation_id: Optional[str] = Field(None, description="Conversation identifier")
    message: Optional[str] = Field(None, description="Associated message")

# Product models
class ProductRecommendationRequest(BaseRequest):
    """Product recommendation request"""
    product_id: str = Field(..., description="Product identifier")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum number of recommendations")
    recommendation_type: str = Field(default="similar", description="Recommendation type")
    
    @validator('recommendation_type')
    def validate_recommendation_type(cls, v):
        allowed_types = ['similar', 'complementary', 'substitute', 'variant']
        if v not in allowed_types:
            raise ValueError(f'recommendation_type must be one of {allowed_types}')
        return v

# Translation models
class TranslationRequest(BaseModel):
    """Text translation request"""
    text: str = Field(..., min_length=1, description="Text to translate")
    target_language: str = Field(..., description="Target language code")
    source_language: Optional[str] = Field(None, description="Source language code")

# Cache models
class CacheOperation(BaseModel):
    """Cache operation request"""
    key: str = Field(..., description="Cache key")
    value: Optional[Any] = Field(None, description="Cache value")
    ttl: Optional[int] = Field(None, description="Time to live in seconds")