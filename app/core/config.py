"""
Application Configuration
Pydantic-based settings with environment variable support
"""
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # App settings
    APP_NAME: str = "Mercury AI Assistant"
    VERSION: str = "4.0.0"
    DEBUG: bool = Field(default=False, alias="DEBUG")
    PORT: int = Field(default=8000, alias="PORT")
    
    # Security
    SECRET_KEY: str = Field(alias="SECRET_KEY")
    
    # Google Cloud & AI
    GOOGLE_API_KEY: str = Field(alias="GOOGLE_API_KEY")
    GOOGLE_CLOUD_PROJECT: Optional[str] = Field(default=None, alias="GOOGLE_CLOUD_PROJECT")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = Field(default=None, alias="GOOGLE_APPLICATION_CREDENTIALS")
    
    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", alias="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, alias="REDIS_PORT")
    REDIS_DB: int = Field(default=0, alias="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    REDIS_URL: Optional[str] = Field(default=None, alias="REDIS_URL")
    
    # Cache TTL settings (in seconds)
    CONVERSATION_CACHE_TTL: int = Field(default=3600, alias="CONVERSATION_CACHE_TTL")
    CONTEXT_CACHE_TTL: int = Field(default=1800, alias="CONTEXT_CACHE_TTL")
    
    # Weather API
    WEATHER_API_KEY: Optional[str] = Field(default=None, alias="WEATHER_API_KEY")
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(default=["*"], alias="ALLOWED_ORIGINS")
    
    # Database URLs (if using SQL databases in future)
    DATABASE_URL: Optional[str] = Field(default=None, alias="DATABASE_URL")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # File upload settings
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, alias="MAX_FILE_SIZE")  # 10MB
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=["image/jpeg", "image/png", "image/gif", "image/webp"],
        alias="ALLOWED_FILE_TYPES"
    )
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    
    # Background task settings
    ENABLE_BACKGROUND_TASKS: bool = Field(default=True, alias="ENABLE_BACKGROUND_TASKS")
    CONVERSATION_CLEANUP_INTERVAL: int = Field(default=300, alias="CONVERSATION_CLEANUP_INTERVAL")  # 5 minutes
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore")

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    # Load .env file from project root
    env_path = Path(__file__).parent.parent.parent / '.env'
    return Settings(_env_file=env_path if env_path.exists() else None)