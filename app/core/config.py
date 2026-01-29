"""
Application Configuration
Pydantic-based settings with environment variable support
"""
import os
from functools import lru_cache
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """Application settings with validation"""
    
    # App settings
    APP_NAME: str = "Walmart AI Assistant"
    VERSION: str = "4.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    PORT: int = Field(default=8000, env="PORT")
    
    # Security
    SECRET_KEY: str = Field(env="SECRET_KEY")
    
    # Google Cloud & AI
    GOOGLE_API_KEY: str = Field(env="GOOGLE_API_KEY")
    GOOGLE_CLOUD_PROJECT: Optional[str] = Field(env="GOOGLE_CLOUD_PROJECT")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = Field(env="GOOGLE_APPLICATION_CREDENTIALS")
    
    # Firestore
    FIRESTORE_COLLECTION: str = Field(default="products", env="FIRESTORE_COLLECTION")
    FIREBASE_CREDENTIALS_PATH: Optional[str] = Field(env="FIREBASE_CREDENTIALS_PATH")
    
    # Google Cloud Storage
    GCS_BUCKET_NAME: str = Field(default="walmart-sparkathon-images", env="GCS_BUCKET_NAME")
    
    # Qdrant Vector Database
    QDRANT_HOST: str = Field(default="localhost", env="QDRANT_HOST")
    QDRANT_PORT: int = Field(default=6333, env="QDRANT_PORT")
    QDRANT_COLLECTION_NAME: str = Field(default="products", env="QDRANT_COLLECTION_NAME")
    QDRANT_API_KEY: Optional[str] = Field(env="QDRANT_API_KEY")
    
    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(env="REDIS_PASSWORD")
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # Cache TTL settings (in seconds)
    CONVERSATION_CACHE_TTL: int = Field(default=3600, env="CONVERSATION_CACHE_TTL")
    CONTEXT_CACHE_TTL: int = Field(default=1800, env="CONTEXT_CACHE_TTL")
    
    # Weather API
    WEATHER_API_KEY: Optional[str] = Field(env="WEATHER_API_KEY")
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(default=["*"], env="ALLOWED_ORIGINS")
    
    # Database URLs (if using SQL databases in future)
    DATABASE_URL: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # File upload settings
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=["image/jpeg", "image/png", "image/gif", "image/webp"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Background task settings
    ENABLE_BACKGROUND_TASKS: bool = Field(default=True, env="ENABLE_BACKGROUND_TASKS")
    CONVERSATION_CLEANUP_INTERVAL: int = Field(default=300, env="CONVERSATION_CLEANUP_INTERVAL")  # 5 minutes
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    # Load .env file from project root
    env_path = Path(__file__).parent.parent.parent.parent / '.env'
    return Settings(_env_file=env_path if env_path.exists() else None)