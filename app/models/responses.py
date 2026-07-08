"""
Response Models
Pydantic models for API response validation
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Base response models
class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = Field(default=True, description="Operation success status")
    message: Optional[str] = Field(None, description="Response message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(default=False, description="Operation success status")
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Error details")
    error_code: Optional[str] = Field(None, description="Error code")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")

# Product models
class ScoreBreakdown(BaseModel):
    """Transparency for search ranking scores"""
    keyword_score: float = Field(0.0, description="Keyword/Exact match score")
    semantic_score: float = Field(0.0, description="Semantic/Vector similarity score")
    rrf_score: float = Field(0.0, description="Reciprocal Rank Fusion combined score")
    personalization_boost: float = Field(0.0, description="Boost from user preferences/history")

class ProductInfo(BaseModel):
    """Product information with ranking transparency"""
    id: str = Field(..., description="Product identifier")
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    brand: Optional[str] = Field(None, description="Product brand")
    category: Optional[str] = Field(None, description="Product category")
    sub_category: Optional[str] = Field(None, description="Product sub-category")
    price: Optional[Dict[str, Any]] = Field(None, description="Price information")
    rating: Optional[float] = Field(None, description="Product rating")
    stock: Optional[Any] = Field(None, description="Stock status")
    images: Optional[List[str]] = Field(None, description="Product images")
    tags: Optional[Any] = Field(None, description="Product tags")
    availability: Optional[List[Dict[str, Any]]] = Field(None, description="Store availability")
    score: float = Field(0.0, description="Search relevance score")
    breakdown: Optional[ScoreBreakdown] = Field(None, description="Ranking score transparency")

class SearchMeta(BaseModel):
    """Search execution metadata"""
    search_id: Optional[str] = Field(None, description="Unique search ID for click telemetry")
    latency_ms: int = Field(..., description="Execution time in milliseconds")
    cache_hit: bool = Field(default=False, description="Whether results came from cache")
    search_mode: str = Field(default="hybrid", description="Search mode used (keyword, semantic, hybrid)")

class SearchResult(BaseResponse):
    """Production-ready search results response"""
    query: str = Field(..., description="Search query")
    results: List[ProductInfo] = Field(..., description="Search results")
    total_results: int = Field(..., description="Total number of results")
    facets: Optional[Dict[str, Dict[str, int]]] = Field(None, description="Aggregated result facets")
    meta: Optional[SearchMeta] = Field(None, description="Execution metadata")
    search_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional search metadata")

# Chat models
class ChatResponse(BaseResponse):
    """Chat response model"""
    response: str = Field(..., description="Assistant response")
    conversation_id: str = Field(..., description="Conversation identifier")
    message_id: str = Field(..., description="Message identifier")
    user_message_id: Optional[str] = Field(None, description="User message identifier")
    personalization_reason: Optional[str] = Field(None, description="Personalization explanation")
    language_info: Optional[Dict[str, str]] = Field(None, description="Language information")
    cache_stats: Optional[Dict[str, Any]] = Field(None, description="Cache statistics")
    features_used: Optional[Dict[str, bool]] = Field(None, description="Features utilized")

# Image models
class ImageAnalysis(BaseModel):
    """Image analysis result"""
    description: str = Field(..., description="Image description")
    is_barcode: bool = Field(default=False, description="Contains barcode")
    barcode_data: Optional[str] = Field(None, description="Barcode value")
    barcode_type: Optional[str] = Field(None, description="Barcode type")
    confidence_score: Optional[float] = Field(None, description="Analysis confidence")

class ImageUploadResponse(BaseResponse):
    """Image upload response"""
    image_id: str = Field(..., description="Image identifier")
    image_url: str = Field(..., description="Image URL")
    analysis: ImageAnalysis = Field(..., description="Image analysis")
    product_data: Optional[ProductInfo] = Field(None, description="Product data if barcode detected")

# User models
class UserProfile(BaseModel):
    """User profile information"""
    user_id: str = Field(..., description="User identifier")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")
    activity_summary: Optional[Dict[str, Any]] = Field(None, description="Activity summary")
    created_at: Optional[datetime] = Field(None, description="Profile creation date")
    last_active: Optional[datetime] = Field(None, description="Last activity date")

class UserProfileResponse(BaseResponse):
    """User profile response"""
    profile: UserProfile = Field(..., description="User profile")

# Conversation models
class ConversationSummary(BaseModel):
    """Conversation summary"""
    conversation_id: str = Field(..., description="Conversation identifier")
    title: Optional[str] = Field(None, description="Conversation title")
    last_message: Optional[str] = Field(None, description="Last message preview")
    message_count: int = Field(default=0, description="Number of messages")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    archived: bool = Field(default=False, description="Archive status")

class ConversationMessage(BaseModel):
    """Conversation message"""
    message_id: str = Field(..., description="Message identifier")
    user_id: str = Field(..., description="User identifier")
    message: str = Field(..., description="Message content")
    message_type: str = Field(default="text", description="Message type")
    timestamp: datetime = Field(..., description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Message metadata")

class ConversationDetail(BaseModel):
    """Detailed conversation information"""
    conversation_id: str = Field(..., description="Conversation identifier")
    title: Optional[str] = Field(None, description="Conversation title")
    messages: List[ConversationMessage] = Field(..., description="Conversation messages")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    archived: bool = Field(default=False, description="Archive status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Conversation metadata")

class ConversationListResponse(BaseResponse):
    """Conversation list response"""
    conversations: List[ConversationSummary] = Field(..., description="User conversations")
    total: int = Field(..., description="Total number of conversations")
    pagination: Optional[Dict[str, Any]] = Field(None, description="Pagination metadata")

class ConversationDetailResponse(BaseResponse):
    """Conversation detail response"""
    conversation: ConversationDetail = Field(..., description="Conversation details")

# WebSocket models
class WebSocketResponse(BaseModel):
    """WebSocket response structure"""
    event: str = Field(..., description="Event type")
    data: Dict[str, Any] = Field(..., description="Response data")
    success: bool = Field(default=True, description="Operation success")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")

class ConnectionResponse(WebSocketResponse):
    """WebSocket connection response"""
    session_id: str = Field(..., description="WebSocket session identifier")
    features: List[str] = Field(..., description="Available features")

# Health check models
class HealthStatus(BaseModel):
    """Health check status"""
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="Application version")
    services: Dict[str, bool] = Field(..., description="Service health status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")

# Cache models
class CacheStats(BaseModel):
    """Cache statistics"""
    total_keys: int = Field(..., description="Total number of keys")
    memory_usage: Optional[str] = Field(None, description="Memory usage")
    hit_rate: Optional[float] = Field(None, description="Cache hit rate")
    connected: bool = Field(..., description="Cache connection status")

class CacheResponse(BaseResponse):
    """Cache operation response"""
    key: str = Field(..., description="Cache key")
    value: Optional[Any] = Field(None, description="Cache value")
    exists: bool = Field(..., description="Key exists in cache")
    ttl: Optional[int] = Field(None, description="Time to live")

# Recommendation models
class RecommendationResponse(BaseResponse):
    """Product recommendation response"""
    product_id: str = Field(..., description="Original product identifier")
    recommendations: List[ProductInfo] = Field(..., description="Recommended products")
    total: int = Field(..., description="Total number of recommendations")
    recommendation_type: str = Field(..., description="Type of recommendations")
    criteria: Optional[Dict[str, Any]] = Field(None, description="Recommendation criteria")

# Translation models
class TranslationResponse(BaseResponse):
    """Translation response"""
    original_text: str = Field(..., description="Original text")
    translated_text: str = Field(..., description="Translated text")
    source_language: str = Field(..., description="Detected/specified source language")
    target_language: str = Field(..., description="Target language")
    confidence: Optional[float] = Field(None, description="Translation confidence")

# Session models
class SessionResponse(BaseResponse):
    """Session start response"""
    session_id: str = Field(..., description="Session identifier")
    greeting: str = Field(..., description="Personalized greeting")
    context: Optional[Dict[str, Any]] = Field(None, description="Session context")
    recommendations: Optional[List[ProductInfo]] = Field(None, description="Initial recommendations")

# Status enums
class MessageStatus(str, Enum):
    """Message delivery status"""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

class ServiceStatus(str, Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

# Pagination models
class PaginationInfo(BaseModel):
    """Pagination information"""
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total: int = Field(..., description="Total number of items")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")

class PaginatedResponse(BaseResponse):
    """Paginated response base"""
    pagination: PaginationInfo = Field(..., description="Pagination information")

# Analytics models
class AnalyticsData(BaseModel):
    """Analytics data"""
    event_type: str = Field(..., description="Event type")
    user_id: Optional[str] = Field(None, description="User identifier")
    properties: Dict[str, Any] = Field(..., description="Event properties")
    timestamp: datetime = Field(default_factory=datetime.now, description="Event timestamp")

class AnalyticsResponse(BaseResponse):
    """Analytics response"""
    events_recorded: int = Field(..., description="Number of events recorded")
    batch_id: Optional[str] = Field(None, description="Batch identifier")