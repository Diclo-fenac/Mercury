from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    query: str = Field(..., max_length=200, description="The search query string.")
    limit: int = Field(default=10, ge=1, le=50, description="Max number of results to return.")
    page: int = Field(default=1, ge=1, description="Page number.")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters.")

class AutocompleteQuery(BaseModel):
    query: str = Field(..., max_length=100, description="Partial query to complete.")
    limit: int = Field(default=5, ge=1, le=20, description="Max completions to return.")

class ProductIdQuery(BaseModel):
    product_id: str = Field(..., description="The ID of the product.")

class RecommendationsQuery(BaseModel):
    product_id: str = Field(..., description="The ID of the reference product.")
    limit: int = Field(default=5, ge=1, le=20, description="Max recommendations to return.")

class ChatQuery(BaseModel):
    message: str = Field(..., max_length=1000, description="The message for the catalog chat.")
    conversation_id: Optional[str] = Field(default=None, description="Optional conversation ID to continue a thread.")
