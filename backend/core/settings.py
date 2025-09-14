"""
Application settings and configuration.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Matchering Player"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Database
    DB_PATH: Path = Path("data/matchering.db")
    
    @property
    def get_db_url(self) -> str:
        """Get database URL."""
        # Ensure the data directory exists
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{self.DB_PATH}"
    
    # Redis
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_URI: Optional[RedisDsn] = None
    
    @property
    def get_redis_url(self) -> str:
        """Get Redis URL."""
        return str(
            RedisDsn.build(
                scheme="redis",
                username="",
                password=self.REDIS_PASSWORD,
                host=self.REDIS_HOST,
                port=self.REDIS_PORT,
                path=f"/{self.REDIS_DB}",
            )
        )
    
    # File storage
    UPLOAD_DIR: Path = Path("/tmp/matchering/uploads")
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    SUPPORTED_FORMATS: List[str] = [".mp3", ".flac", ".wav", ".aiff"]
    
    # WebSocket
    WS_MESSAGE_QUEUE: str = "matchering:ws:queue"
    WS_HEARTBEAT_INTERVAL: int = 30
    
    # Processing
    PROCESSING_QUEUE: str = "matchering:processing:queue"
    MAX_PROCESSING_TIME: int = 300  # 5 minutes
    DEFAULT_SAMPLE_RATE: int = 44100
    DEFAULT_BIT_DEPTH: int = 24
    
    # Cache
    CACHE_TTL: int = 300  # 5 minutes
    CACHE_PREFIX: str = "matchering:cache:"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_prefix="MATCHERING_",
    )
    
    def get_cache_key(self, key: str) -> str:
        """Get cache key with prefix."""
        return f"{self.CACHE_PREFIX}{key}"

settings = Settings()
