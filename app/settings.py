"""
Application Settings
Environment configuration with validation
"""
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # App settings
    APP_NAME: str = "Mercury AI Assistant"
    VERSION: str = "4.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    PORT: int = Field(default=8000, env="PORT")
    MERCURY_MODE: str = Field(default="standard", env="MERCURY_MODE")
    
    # Security
    SECRET_KEY: str = Field(env="SECRET_KEY")
    
    # Google Cloud & AI
    GOOGLE_API_KEY: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    GEMINI_API_KEY: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    GEMINI_MODEL_NAME: str = Field(default="gemini-1.5-pro", env="GEMINI_MODEL_NAME")
    GOOGLE_CLOUD_PROJECT: Optional[str] = Field(default=None, env="GOOGLE_CLOUD_PROJECT")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = Field(default=None, env="GOOGLE_APPLICATION_CREDENTIALS")
    GEMINI_EMBEDDING_MODEL: str = Field(default="models/text-embedding-002", env="GEMINI_EMBEDDING_MODEL")

    # Vision settings
    VISION_PROVIDER: str = Field(default="gemini", env="VISION_PROVIDER") # gemini | openai | local
    VISION_API_KEY: Optional[str] = Field(default=None, env="VISION_API_KEY")
    VISION_API_BASE: Optional[str] = Field(default=None, env="VISION_API_BASE")
    VISION_MODEL_NAME: str = Field(default="gemini-2.5-flash", env="VISION_MODEL_NAME")

    # PostgreSQL Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://mercury:mercury_dev_password@localhost:5432/mercury",
        env="DATABASE_URL"
    )

    # MinIO Storage
    MINIO_ENDPOINT: Optional[str] = Field(default=None, env="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: Optional[str] = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: Optional[str] = Field(default="minioadmin", env="MINIO_SECRET_KEY")
    MINIO_BUCKET_NAME: str = Field(default="mercury-uploads", env="MINIO_BUCKET_NAME")
    MINIO_SECURE: bool = Field(default=False, env="MINIO_SECURE")

    # Typesense Search
    TYPESENSE_HOST: str = Field(default="localhost", env="TYPESENSE_HOST")
    TYPESENSE_PORT: int = Field(default=8108, env="TYPESENSE_PORT")
    TYPESENSE_API_KEY: str = Field(default="xyz", env="TYPESENSE_API_KEY")
    TYPESENSE_SEARCH_API_KEY: Optional[str] = Field(default=None, env="TYPESENSE_SEARCH_API_KEY")

    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, env="REDIS_PORT")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_URL: Optional[str] = Field(default=None, env="REDIS_URL")

    
    # Cache TTL settings (in seconds)
    CONVERSATION_CACHE_TTL: int = Field(default=3600, env="CONVERSATION_CACHE_TTL")
    CONTEXT_CACHE_TTL: int = Field(default=1800, env="CONTEXT_CACHE_TTL")
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(default=["*"], env="ALLOWED_ORIGINS")
    WS_ALLOWED_ORIGINS: List[str] = Field(default=["*"], env="WS_ALLOWED_ORIGINS")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    PROMETHEUS_ENABLED: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    
    # File upload settings
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=["image/jpeg", "image/png", "image/gif", "image/webp"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Feature Flags
    FEATURE_FLAGS: List[str] = Field(default=["vector-search", "semantic-ranking"], env="FEATURE_FLAGS")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    env_path = Path(__file__).parent.parent / '.env'
    return Settings(_env_file=env_path if env_path.exists() else None)
