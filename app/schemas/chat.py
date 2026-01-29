"""
Chat Schemas
Request/Response models for chat endpoints
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class ChatRequest(BaseModel):
    """Chat message request"""
    message: str = Field(..., min_length=1, max_length=5000)
    user_id: str = Field(...)
    conversation_id: Optional[str] = None
    message_type: str = Field(default="text")
    image_data: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @validator('message_type')
    def validate_message_type(cls, v):
        allowed = ['text', 'image']
        if v not in allowed:
            raise ValueError(f'message_type must be one of {allowed}')
        return v


class ChatResponse(BaseModel):
    """Chat response"""
    response: str
    conversation_id: str
    message_id: str
    user_message_id: Optional[str] = None
    personalization_reason: Optional[str] = None
    features_used: Optional[Dict[str, bool]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ConversationHistoryRequest(BaseModel):
    """Get conversation history"""
    conversation_id: str
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class ConversationHistoryResponse(BaseModel):
    """Conversation history response"""
    conversation_id: str
    messages: list
    total: int
    has_more: bool
