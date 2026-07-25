"""
Application Settings
Environment configuration with validation
"""
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # App settings
    APP_NAME: str = "Mercury AI Assistant"
    VERSION: str = "4.0.0"
    DEBUG: bool = Field(default=False, alias="DEBUG")
    TEST_MODE: bool = Field(default=False, alias="MERCURY_TEST_MODE")
    PORT: int = Field(default=8000, alias="PORT")
    MERCURY_MODE: str = Field(default="standard", alias="MERCURY_MODE")
    
    # Security
    SECRET_KEY: str = Field(default="dev_secret_key_mercury_v1_change_in_production_9999", alias="SECRET_KEY")
    
    # Google Cloud & AI
    GOOGLE_API_KEY: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    GEMINI_API_KEY: str = Field(default="", alias="GEMINI_API_KEY")
    GEMINI_MODEL_NAME: str = Field(default="gemini-1.5-pro", alias="GEMINI_MODEL_NAME")
    GOOGLE_CLOUD_PROJECT: Optional[str] = Field(default=None, alias="GOOGLE_CLOUD_PROJECT")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = Field(default=None, alias="GOOGLE_APPLICATION_CREDENTIALS")
    GEMINI_EMBEDDING_MODEL: str = Field(default="gemini-embedding-2", alias="GEMINI_EMBEDDING_MODEL")
    EMBEDDING_PROVIDER: str = Field(default="gemini", alias="EMBEDDING_PROVIDER")

    # Intelligence settings
    AI_PROVIDER: str = Field(default="gemini", alias="AI_PROVIDER")

    # Vision settings
    VISION_PROVIDER: str = Field(default="gemini", alias="VISION_PROVIDER") # gemini | openai | local
    VISION_API_KEY: Optional[str] = Field(default=None, alias="VISION_API_KEY")
    VISION_API_BASE: Optional[str] = Field(default=None, alias="VISION_API_BASE")
    VISION_MODEL_NAME: str = Field(default="gemini-2.5-flash", alias="VISION_MODEL_NAME")

    # PostgreSQL Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://mercury:mercury_dev_password@localhost:5432/mercury",
        alias="DATABASE_URL"
    )

    # MinIO Storage
    MINIO_ENDPOINT: Optional[str] = Field(default=None, alias="MINIO_ENDPOINT")
    MINIO_ACCESS_KEY: Optional[str] = Field(default="minioadmin", alias="MINIO_ACCESS_KEY")
    MINIO_SECRET_KEY: Optional[str] = Field(default="minioadmin", alias="MINIO_SECRET_KEY")
    MINIO_BUCKET_NAME: str = Field(default="mercury-uploads", alias="MINIO_BUCKET_NAME")
    MINIO_SECURE: bool = Field(default=False, alias="MINIO_SECURE")

    # Typesense Search
    TYPESENSE_HOST: str = Field(default="localhost", alias="TYPESENSE_HOST")
    TYPESENSE_PORT: int = Field(default=8108, alias="TYPESENSE_PORT")
    TYPESENSE_API_KEY: str = Field(default="xyz", alias="TYPESENSE_API_KEY")
    TYPESENSE_SEARCH_API_KEY: Optional[str] = Field(default=None, alias="TYPESENSE_SEARCH_API_KEY")

    # Redis Configuration
    REDIS_HOST: str = Field(default="localhost", alias="REDIS_HOST")
    REDIS_PORT: int = Field(default=6379, alias="REDIS_PORT")
    REDIS_DB: int = Field(default=0, alias="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(default=None, alias="REDIS_PASSWORD")
    REDIS_URL: Optional[str] = Field(default=None, alias="REDIS_URL")

    
    # Cache TTL settings (in seconds)
    CONVERSATION_CACHE_TTL: int = Field(default=3600, alias="CONVERSATION_CACHE_TTL")
    CONTEXT_CACHE_TTL: int = Field(default=1800, alias="CONTEXT_CACHE_TTL")

    # Durable catalog indexing outbox
    CATALOG_INDEX_WORKER_ENABLED: bool = Field(default=True, alias="CATALOG_INDEX_WORKER_ENABLED")
    CATALOG_INDEX_POLL_INTERVAL_SECONDS: int = Field(
        default=5, ge=1, alias="CATALOG_INDEX_POLL_INTERVAL_SECONDS"
    )
    CATALOG_INDEX_BATCH_SIZE: int = Field(default=100, ge=1, le=1000, alias="CATALOG_INDEX_BATCH_SIZE")
    CATALOG_INDEX_LEASE_SECONDS: int = Field(default=60, ge=5, alias="CATALOG_INDEX_LEASE_SECONDS")
    CATALOG_INDEX_MAX_ATTEMPTS: int = Field(default=10, ge=1, alias="CATALOG_INDEX_MAX_ATTEMPTS")
    
    # CORS settings
    ALLOWED_ORIGINS: Union[str, List[str]] = Field(default=["*"], alias="ALLOWED_ORIGINS")
    WS_ALLOWED_ORIGINS: Union[str, List[str]] = Field(default=["*"], alias="WS_ALLOWED_ORIGINS")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", alias="LOG_LEVEL")
    PROMETHEUS_ENABLED: bool = Field(default=True, alias="PROMETHEUS_ENABLED")
    
    # File upload settings
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024, alias="MAX_FILE_SIZE")  # 10MB
    ALLOWED_FILE_TYPES: Union[str, List[str]] = Field(
        default=["image/jpeg", "image/png", "image/gif", "image/webp"],
        alias="ALLOWED_FILE_TYPES"
    )
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    
    # MCP Settings
    MCP_ENABLED: bool = Field(default=True, alias="MCP_ENABLED")
    MCP_REGIONAL_ENDPOINT: str = Field(default="https://api.mercury.local", alias="MCP_REGIONAL_ENDPOINT")
    MCP_OIDC_ISSUER: Optional[str] = Field(default=None, alias="MCP_OIDC_ISSUER")
    MCP_OIDC_AUDIENCE: Optional[str] = Field(default=None, alias="MCP_OIDC_AUDIENCE")
    MCP_TOKEN_EXPIRY_MINUTES: int = Field(default=60, alias="MCP_TOKEN_EXPIRY_MINUTES")

    # Feature Flags
    FEATURE_FLAGS: Union[str, List[str]] = Field(default=["vector-search", "semantic-ranking"], alias="FEATURE_FLAGS")
    
    @field_validator("ALLOWED_ORIGINS", "WS_ALLOWED_ORIGINS", "ALLOWED_FILE_TYPES", "FEATURE_FLAGS", mode="before")
    @classmethod
    def parse_list_from_str(cls, v):
        if isinstance(v, str):
            if v.strip().startswith("[") and v.strip().endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    env_path = Path(__file__).parent.parent / '.env'
    return Settings(_env_file=env_path if env_path.exists() else None)
